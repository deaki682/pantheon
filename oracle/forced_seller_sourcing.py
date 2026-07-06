"""Forced-seller event sourcing — Oracle's coverage spine (2026-07-06).

Fixes the sourcing bottleneck the 2026-07-06 launch gate exposed. Oracle's four
lenses (insider / 13F / 13D / quality) are a narrow, biased net: they surface
only names that trip one of those signals, they miss most of the universe, and
the house has measured them at ~zero mechanical alpha. The durable convex edges
do not live there — they live in STRUCTURAL forced-seller events, where a
counterparty must sell for reasons unrelated to value. And those are findable
EXHAUSTIVELY, because every one leaves a filing trail.

This generalizes the proven `nemesis.spinoffs` scanner (EDGAR full-text search →
deduped CIK-keyed pipeline) into a multi-family sweep across every LIVE
forced-seller channel — the "widen the net" half of the rebuild. Every candidate
it emits still faces the full convex-dossier + primary-source verification gate
built the same day (`make_convex_dossier` → `verify_dossier` → `rank_fundable`):
this widens coverage, the gate keeps it honest, and they compose.

Two disciplines are baked in, because tonight's diligence bought them dearly:

  1. THE GRAVEYARD. Several forced-seller families are already REFUTED
     house-wide (see docs/RESEARCH_LEDGER.md). Sourcing must NEVER re-surface a
     dead family — that spends the error budget the ledger exists to protect.
     Encoded in GRAVEYARD with the ledger reason; enforced in `sweep`.

  2. DOMAIN SEPARATION. Cash-merger targets belong to Hermes (its live A/B),
     not Oracle. Excluded so the two gods never double-source the same name.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from nemesis.spinoffs import events_from_search_payload  # generic FTS-hit parser
from shared import edgar


@dataclass(frozen=True)
class Family:
    """One forced-seller channel: an EDGAR full-text query + form filter, and
    the structural reason its flow is price-insensitive."""
    key: str
    label: str
    query: str
    forms: tuple[str, ...]
    mechanism: str          # who is forced to sell, and why (the G2 constraint)
    note: str = ""          # live-status caveat / size filter / ledger pointer


# ---------------------------------------------------------------------------
# THE GRAVEYARD — forced-seller families the house already REFUTED. Never
# sourced. Key = the refuted lab slug or family; value = the one-line verdict +
# ledger pointer. `sweep` refuses to emit any candidate tagged to these.
# ---------------------------------------------------------------------------
GRAVEYARD: dict[str, str] = {
    "spinoff_orphans": (
        "REFUTED 2026-07-05: small/micro spun-off CHILDREN underperform "
        "size-matched EW -9.3% (holdout -22.6%). The LARGE-cap parent-carveout "
        "channel is NOT refuted; the small-child tail is. See RESEARCH_LEDGER."
    ),
    "cef_tender_convergence": (
        "REFUTED 2026-07-04, wrong sign (-1.81% CAR, t -3.91). Closed-end-fund "
        "issuer self-tenders (SC TO-I) are dead; the odd-lot carve-out is a "
        "DISTINCT, still-live mechanic. See RESEARCH_LEDGER."
    ),
    "ipo_lockup_reversion": (
        "REFUTED (terminal): -10.4% mean excess. IPO lockup-expiry reversal is "
        "dead — do not source it as a forced-seller edge."
    ),
    "sp500_index_addition": (
        "REFUTED/DECAYED: the S&P index-ADDITION forced-buy effect is dead in "
        "the deployable window. (Index DELETIONS — forced SELLING — are a "
        "distinct, less-studied mechanic and are not in this graveyard.)"
    ),
    "cvr_arb": "NEVER PROPOSE: compound forecast w/ adversarial payer (Celgene $9->$0); not a contract.",
    "short_vol_vrp": "NEVER PROPOSE: anti-convex for a long-only floor book.",
}

# Cash-merger targets are HERMES's domain (its live merger-arb A/B), not Oracle's.
HERMES_DOMAIN_KEY = "merger_target"


# ---------------------------------------------------------------------------
# LIVE families — the channels Oracle sources. Each is either not-yet-tested or
# a structurally distinct, non-refuted mechanic. Size/subset caveats that keep a
# channel clear of its graveyard neighbor are in `note`.
# ---------------------------------------------------------------------------
LIVE_FAMILIES: tuple[Family, ...] = (
    Family(
        key="spinoff_largecap",
        label="Large-cap spinoff carve-out",
        query="spin-off",
        forms=("10-12B",),
        mechanism="Parent holders receive a stub they can't/won't hold; index "
                  "funds must sell it if it doesn't qualify for the parent's index.",
        note="LARGE-cap carve-outs only — the SMALL spun-off child tail is "
             "graveyard (spinoff_orphans). Size-filter candidates before dossier. "
             "Overlaps nemesis.spinoffs pipeline; dedupe against it.",
    ),
    Family(
        key="post_bk_emergence",
        label="Post-bankruptcy emergence equity",
        query="plan of reorganization emergence",
        forms=("8-K",),
        mechanism="CLO/credit indentures force divestiture of reorg equity "
                  "distributed to former creditors who cannot hold equity.",
        note="LAB_HYPOTHESIS, open (population inadequate on first pass — needs "
             "a survivorship-complete build). Not refuted; source with care.",
    ),
    Family(
        key="rights_offering",
        label="Dilutive rights offering",
        query="subscription rights offering",
        forms=("424B3", "424B4", "S-1"),
        mechanism="Non-subscribing holders are diluted; the overhang and "
                  "record-date mechanics create price-insensitive supply.",
        note="Untested house-wide. The GYRO-style dilution mechanic — but here "
             "as a forward event, not a melting liquidation. New channel.",
    ),
    Family(
        key="fund_liquidation",
        label="Closed-end fund / BDC wind-down",
        query="plan of liquidation orderly wind-down",
        forms=("8-K", "N-8F"),
        mechanism="A terminating fund must sell holdings and close its own "
                  "discount to NAV by a dated deadline — a contractual pull-to-NAV.",
        note="DISTINCT from cef_tender_convergence (graveyard): a full "
             "liquidation/termination is a dated pull-to-NAV, not an issuer "
             "self-tender. Verify the discount is real (not a par-priced bond fund).",
    ),
    Family(
        key="odd_lot_tender",
        label="Odd-lot tender / Dutch-auction carve-out",
        query="odd lot",
        forms=("SC TO-I", "SC TO-C"),
        mechanism="Rule 13e-4 odd-lot provision: <100-share holders tender "
                  "un-proratable at the top price — an issuer contractually bound.",
        note="LAB_HYPOTHESIS (live, supply-starved ~1%/yr ceiling). "
             "Opportunistic-only; never a full position.",
    ),
)


def family_by_key(key: str) -> Optional[Family]:
    return next((f for f in LIVE_FAMILIES if f.key == key), None)


def is_graveyard(key: str) -> bool:
    """True if the family key is a refuted/never-propose family, or Hermes's."""
    return key in GRAVEYARD or key == HERMES_DOMAIN_KEY


# ---------------------------------------------------------------------------
# Search + sweep
# ---------------------------------------------------------------------------
def search_family(
    family: Family, date_from: str, date_to: str, *,
    max_hits: int = 500,
    search_fn: Callable[..., dict] = edgar.search_filings,
) -> list[dict]:
    """Paged EDGAR full-text search for one family → candidate dicts.

    Generalizes nemesis.spinoffs.search_spinoff_registrations to any
    (query, forms). `search_fn` is injectable so tests feed captured payloads
    with no network. EDGAR FTS pages at 10 hits and 500s intermittently; a
    partial sweep beats a dead one (the cadence re-covers the window)."""
    hits: list[dict] = []
    offset = 0
    while True:
        try:
            payload = search_fn(
                family.query, forms=list(family.forms),
                date_from=date_from, date_to=date_to, offset=offset,
            )
        except Exception:
            break
        page = payload.get("hits", {}).get("hits", [])
        hits.extend(page)
        total = payload.get("hits", {}).get("total", {}).get("value", 0)
        offset += len(page)
        if not page or offset >= total or offset >= max_hits:
            break
    return [_candidate(e, family) for e in events_from_search_payload({"hits": {"hits": hits}})]


def _candidate(event, family: Family) -> dict:
    """A SpinEvent-shaped parse → a family-tagged sourcing candidate."""
    return {
        "cik": event.cik,
        "ticker": event.ticker,
        "company": event.company,
        "family": family.key,
        "family_label": family.label,
        "mechanism": family.mechanism,
        "first_filed": event.first_filed,
        "last_filed": event.last_filed,
        "n_filings": event.n_filings,
        "note": family.note,
    }


def sweep(
    date_from: str, date_to: str, *,
    families: tuple[Family, ...] = LIVE_FAMILIES,
    exclude_ciks: Optional[set[str]] = None,
    search_fn: Callable[..., dict] = edgar.search_filings,
) -> list[dict]:
    """Sweep every LIVE forced-seller family over [date_from, date_to] → one
    deduped, graveyard-clean candidate list feeding the dossier→verify pipeline.

    - Refuses any family in the graveyard / Hermes's domain (defense in depth:
      LIVE_FAMILIES already excludes them, but a caller passing a bad family is
      dropped here too).
    - Dedupes by CIK across families; a name hitting multiple channels keeps the
      union of family tags (a name that's BOTH a spinoff and a rights offering
      is a stronger lead, not two).
    - `exclude_ciks`: skip names already tracked (e.g. the nemesis pipeline or
      the current dossier pool) so the sweep surfaces only what's NEW.
    """
    exclude = exclude_ciks or set()
    by_cik: dict[str, dict] = {}
    for fam in families:
        if is_graveyard(fam.key):
            continue
        for cand in search_family(fam, date_from, date_to, search_fn=search_fn):
            cik = cand["cik"]
            if not cik or cik in exclude:
                continue
            if cik in by_cik:
                # merge family tags — a multi-channel name is a stronger lead
                existing = by_cik[cik]
                fams = set(existing.get("families", [existing["family"]]))
                fams.add(cand["family"])
                existing["families"] = sorted(fams)
                existing.setdefault("family_labels", [existing["family_label"]])
                if cand["family_label"] not in existing["family_labels"]:
                    existing["family_labels"].append(cand["family_label"])
            else:
                cand["families"] = [cand["family"]]
                cand["family_labels"] = [cand["family_label"]]
                by_cik[cik] = cand
    # multi-channel names first, then oldest filing (closest to actionable)
    return sorted(by_cik.values(),
                  key=lambda c: (-len(c.get("families", [])), c.get("first_filed", "")))
