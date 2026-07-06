"""Fundability prior — the ranker that decides which sourced candidates the
precision stage spends a primary-source verification on (2026-07-06).

The COVERAGE stage sources wide (net-cash + tangible-book + land/asset-NAV). The
PRECISION stage can only verify a handful per session, so something has to RANK
the queue. Raw discount is the wrong ranker (it puts the deepest-discount TRAPS
first — the phantom-debt / stale-count / crypto-shell names). This prior scores
each candidate by:

    prior = discount_score(sweet_spot) * floor_weight * clean * cap_weight

so a moderate discount on a HARD floor with clean flags outranks an 85%-off trap.

THE BUG THIS FIXES (2026-07-06, found via FPH). The first cut of this prior read
the discount only from `floor_usd` (the net-cash/tangible-book path). But
asset-revaluation candidates carry their floor as `nav_at_cost_usd`, NOT
`floor_usd` — so `discount` came back None and the ENTIRE land/asset-NAV family
scored as zero-discount and sank below every net-cash name. FPH — a California
land developer at 3.86x asset coverage (~74% below land-NAV-at-cost, the deepest
in the queue and the prior run's single best verified FUND at convexity 0.131) —
ranked #18 and was cut from verification. The asset_revaluation lens was built
and then made invisible to the ranker that feeds it. `candidate_discount()` now
falls back to the nav_at_cost / asset_coverage path, so the land family is ranked
on its REAL discount. NOTE the precision stage still must separate cost-
UNDERSTATES-value (land developers: raw/entitled land at historical cost) from
cost-OVERSTATES-value (office REITs: cost above a re-rated-down market) — that is
a per-name NAV read, not something the screen can do; the prior's job is only to
stop burying the family so the verifier gets to look at all.
"""
from __future__ import annotations

from typing import Optional

# Reward the sweet-spot discount, penalize the deep-discount trap zone. A 25-65%
# discount is where real neglect lives; >80% is where the phantom-debt / stale-
# count / going-concern traps cluster (measured — every launch-gate kill sat >80%).
SWEET_LO, SWEET_HI, TRAP_HI = 0.25, 0.65, 0.80
# floor trust-ladder weights (mirror convex_dossier.FLOOR_BASIS intent): countable
# cash hardest, land/asset-at-cost medium-soft (needs a transacting mark), resource
# reserves softest.
FLOOR_W = {
    "net_cash": 1.0, "ncav": 0.9, "net_net": 0.9, "cash": 1.0,
    "tangible_book": 0.55, "book": 0.55,
    "asset_land": 0.70, "transacting_asset": 0.70, "asset_resource": 0.40,
    # office/retail/hotel REITs where cost OVERSTATES a re-rated market — cost is a
    # ceiling, not a floor; surfaced but heavily down-trusted so they don't
    # monopolize the land-NAV verification slots (2026-07-06 audit fix).
    "asset_suspect": 0.30,
}
# cap weighting — micro-caps below this are illiquid/manipulable (down-weight);
# names above the neglect ceiling are less likely to be genuinely uncovered.
MICRO_CAP_USD = 20e6
LARGE_CAP_USD = 3_000e6


def candidate_discount(cand: dict) -> Optional[float]:
    """The discount the prior should rank on — floor-agnostic. Prefers an
    explicit `discount`; else 1 - marketcap/floor for net-cash/tangible-book
    names; else the ASSET-REVAL path (1 - marketcap/nav_at_cost, i.e. the land/
    asset-NAV discount) so the land family is not scored as zero. Returns None
    only when neither a floor nor a nav-at-cost is present."""
    d = cand.get("discount")
    if d is not None:
        return float(d)
    mc = cand.get("marketcap_usd")
    if mc and mc > 0:
        floor = cand.get("floor_usd")
        if floor and floor > 0:
            return 1.0 - mc / floor
        # asset-reval fallback — the FPH fix: use nav_at_cost.
        nav = cand.get("nav_at_cost_usd")
        if nav and nav > 0:
            return 1.0 - mc / nav
    # coverage already encodes nav/marketcap — usable even without a marketcap.
    cov = cand.get("asset_coverage")
    if cov and cov > 0:
        return 1.0 - 1.0 / cov
    return None


# The caution/trap band is calibrated on NET-CASH names: >80% below countable cash
# is where phantom-debt / stale-count / going-concern traps cluster, so a deep
# net-cash discount is a yellow flag. But a floor measured at HISTORICAL COST (land,
# resource reserves) is already conservative, so a DEEPER discount to cost is a
# stronger margin of safety, not a trap signal — the failure mode there is
# cost-OVERSTATES (handled separately by the suspect family), not too-deep. So for
# asset-cost floors the sweet spot extends higher before any penalty (2026-07-06
# calibration fix — this is why FPH at 74% below land-NAV-at-cost is no longer
# penalized like an 74%-below-net-cash trap).
_COST_BASIS_FAMILIES = {"land_nav", "resource_nav"}
_ASSET_SWEET_HI = 0.85


def discount_score(discount: Optional[float], *, family: str = "") -> float:
    """1.0 across the sweet spot, ramping to 0 below it, and DECAYING toward the
    trap zone above it — a deep discount is a yellow flag on a CASH floor. For
    cost-basis floors (land/resource) the sweet spot extends to _ASSET_SWEET_HI
    because a deeper discount to conservative cost is a stronger margin, not a trap."""
    if discount is None:
        return 0.0
    d = float(discount)
    if d <= 0:
        return 0.0
    sweet_hi = _ASSET_SWEET_HI if family in _COST_BASIS_FAMILIES else SWEET_HI
    if d < SWEET_LO:
        return d / SWEET_LO                      # 0..1 ramp into the sweet spot
    if d <= sweet_hi:
        return 1.0                               # sweet spot
    if d <= TRAP_HI and sweet_hi < TRAP_HI:
        # linear decay 1.0 -> 0.5 across (sweet_hi, 0.80] caution band
        return 1.0 - 0.5 * (d - sweet_hi) / (TRAP_HI - sweet_hi)
    # trap zone: >80% off -> heavily discounted (every launch-gate KILL sat here),
    # decaying 0.5 -> 0.15 across (0.80, 1.0].
    return max(0.15, 0.5 - 2.0 * (d - TRAP_HI))


def floor_weight(cand: dict) -> float:
    ft = (cand.get("floor_type") or "").lower()
    if ft in FLOOR_W:
        return FLOOR_W[ft]
    # asset-reval names may carry a null floor_type but a nav_at_cost -> land basis
    if cand.get("nav_at_cost_usd") or cand.get("asset_coverage"):
        return FLOOR_W["asset_land"]
    return 0.55


def clean_weight(cand: dict) -> float:
    """Erode the score for the soft-flags the screen raised (dilution, investments-
    heavy, eroding book, book-contradicts-floor, crypto, stale marketcap)."""
    w = 1.0
    if cand.get("recent_dilution"):
        w *= 0.6
    if cand.get("investments_heavy"):
        w *= 0.5
    if cand.get("eroding_book"):
        w *= 0.6
    if cand.get("book_contradicts_floor"):
        w *= 0.4
    if cand.get("crypto_treasury") or cand.get("crypto_name"):
        w *= 0.2
    if cand.get("stale_marketcap"):
        w *= 0.5
    if cand.get("cost_overstates"):      # office/retail REIT — cost is a ceiling
        w *= 0.4
    if cand.get("commodity_dependent"):  # reserve value swings with strip price
        w *= 0.7
    return w


def cap_weight(cand: dict) -> float:
    mc = cand.get("marketcap_usd") or 0
    if mc <= 0:
        return 0.5
    if mc < MICRO_CAP_USD:
        return 0.5
    if mc <= LARGE_CAP_USD:
        return 1.0
    return 0.7


def fundability_prior(cand: dict) -> float:
    """The ranker: sweet-spot discount x floor-hardness x clean-flags x cap. Now
    floor-agnostic in the discount term (asset-reval names ranked on their real
    land-NAV discount) and family-aware in the sweet spot (cost-basis floors get
    the extended band)."""
    return (discount_score(candidate_discount(cand), family=candidate_family(cand))
            * floor_weight(cand) * clean_weight(cand) * cap_weight(cand))


def rank_candidates(cands: list[dict]) -> list[dict]:
    """Return candidates sorted by the fundability prior, best first, each stamped
    with `fundability` and the `rank_discount` it was scored on (for audit)."""
    out = []
    for c in cands:
        c = dict(c)
        c["rank_discount"] = candidate_discount(c)
        c["fundability"] = round(fundability_prior(c), 4)
        out.append(c)
    # Primary: fundability. Secondary (tiebreak): deeper discount first — within the
    # saturated sweet-spot band many names tie on fundability, and the deeper
    # discount is the larger margin of safety, so it should win its verification
    # slot deterministically rather than by list order (2026-07-06 fix — this is
    # why FPH/SDHC/AFCG, the deepest-coverage land names, now lead land_nav instead
    # of sinking to the arbitrary bottom of a 16-way tie).
    return sorted(out, key=lambda c: (-c["fundability"], -(c.get("rank_discount") or -9)))


# ---------------------------------------------------------------------------
# Per-family verification budgets (2026-07-06, the FPH fix, part 2).
#
# A SINGLE blended ranker cannot serve two different edges. net_cash floors
# (weight 1.0) always outrank asset_land floors (0.70) at equal discount, and the
# discount_score saturates flat across the sweet spot, so the net-cash pile fills
# the whole verification budget before the ranker reaches the first land name.
# Result: the asset-revaluation leg gets sourced but never verified — FPH (the
# prior run's best FUND) sank to #140. The two-stage machine's whole premise is
# "source wide across families, leave nothing convex behind." So the precision
# stage must reserve slots PER FAMILY, not run one global top-N.
FLOOR_FAMILY = {
    "net_cash": "net_cash", "ncav": "net_cash", "net_net": "net_cash", "cash": "net_cash",
    "tangible_book": "tangible_book", "book": "tangible_book",
    "asset_land": "land_nav", "transacting_asset": "land_nav",
    "asset_resource": "resource_nav",
    # suspect (cost-overstates) property types get their OWN family so they never
    # crowd out genuine land developers in the land_nav budget.
    "asset_suspect": "suspect_nav",
}


def candidate_family(cand: dict) -> str:
    ft = (cand.get("floor_type") or "").lower()
    if ft in FLOOR_FAMILY:
        return FLOOR_FAMILY[ft]
    if cand.get("nav_at_cost_usd") or cand.get("asset_coverage"):
        return "land_nav"
    return "tangible_book"


def rank_by_family(cands: list[dict], per_family: int = 8) -> dict[str, list[dict]]:
    """Rank within each floor family and keep the top `per_family` of each, so a
    land/asset-NAV name is never buried under the net-cash pile. Returns
    {family: [ranked candidates]}."""
    ranked = rank_candidates(cands)
    fams: dict[str, list[dict]] = {}
    for c in ranked:
        fams.setdefault(candidate_family(c), []).append(c)
    return {f: rows[:per_family] for f, rows in fams.items()}


def verification_queue(cands: list[dict], per_family: int = 8) -> list[dict]:
    """The precision-stage queue: the per-family top-N, interleaved so each family
    gets a fair share of the verification budget rather than net-cash monopolizing
    it. This is what the runbook should verify, NOT a global top-N."""
    fams = rank_by_family(cands, per_family=per_family)
    # round-robin interleave across families by their internal rank
    order = sorted(fams.keys())
    out, i = [], 0
    while True:
        added = False
        for f in order:
            if i < len(fams[f]):
                out.append(fams[f][i]); added = True
        if not added:
            break
        i += 1
    return out
