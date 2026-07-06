"""Hard-catalyst sourcing — the value-realization leg (2026-07-06).

The third why_mispriced type. Where the NEGLECT leg finds names below a floor
with NO catalyst (the mispricing is structural inattention) and the FORCED_SELLER
leg finds price-insensitive SUPPLY, this leg finds names with a dated, filed
CATALYST that will close a discount: an activist who has filed a 13D to force
value realization, or a board that has announced a strategic-alternatives / sale
process. The convex shape is a bounded floor (the standalone business) plus a
catalyst with a clock on it (the campaign / the process).

Like the forced-seller leg, the spine is FORM ENUMERATION off EDGAR's daily
indexes — a SC 13D **is** an activist position, so enumerate every one rather than
keyword-hunt (the measured 12%-recall trap). It reuses
`forced_seller_sourcing.enumerate_by_form` / `cik_to_ticker_map` so there is one
index parser, one tradability filter, one graveyard discipline.

TWO honest constraints, stated not hidden:

  1. SC 13D IS HIGH-VOLUME AND MOSTLY NOT A CAMPAIGN. Enumeration gives 100%
     recall of activist stakes but most 13Ds are passive-ish stake builds, not
     value-realization campaigns. The signal lives in the 13D's **Item 4
     (Purpose of Transaction)** — a per-name read the precision stage does, NOT
     something the index can rank. This leg SOURCES the population; it does not
     assert a campaign. Every candidate carries `requires_item4_read=True`.

  2. THE CATALYST MUST NOT HAVE ALREADY FIRED. An activist 13D or a
     sale-process 8-K that already popped the stock has forfeited the convexity
     (the BOLD/SMHI trap the verification gate guards with `catalyst_fired`).
     This leg surfaces the FILING; the dossier stage checks the price hasn't
     already re-rated.

Everything is a pure function of the daily index (injected `http_get`) — no
hidden network, fully testable.
"""
from __future__ import annotations

from typing import Callable, Optional

from oracle import forced_seller_sourcing as fss
from shared import edgar

# Forms that ARE a value-realization catalyst -> the family. SC 13D (and its
# amendments) are the activist spine; 13D/A escalations are often where a passive
# stake turns into a campaign, so both are enumerated. Deliberately NOT here:
# SC 13G (passive/institutional — no campaign, by rule), SC 14D9 (target response
# to a THIRD-PARTY tender = a merger, Hermes's domain), PREM14A / DEFM14A (merger
# proxies = Hermes). Strategic-review announcements have no single form (they live
# in 8-K Item 1.01/8.01 prose) and are handled by the keyword supplement below.
CATALYST_FORM_TO_FAMILY = {
    "SC 13D": "activist_13d", "SC 13D/A": "activist_13d",
}

# Keyword supplement (the families with no single defining form). Mirrors the
# forced-seller keyword sweep: an 8-K announcing a board-run process. Retained as
# a SUPPLEMENT only — form enumeration is the recall spine.
STRATEGIC_REVIEW = fss.Family(
    key="strategic_review",
    label="Strategic-alternatives / sale process",
    query="exploring strategic alternatives sale process",
    forms=("8-K",),
    mechanism="A board has publicly opened a process to sell/merge/spin the "
              "company — a dated, self-imposed catalyst that pulls price toward "
              "an in-play valuation, distinct from a completed merger (Hermes).",
    note="Keyword supplement (no single defining form). Verify the process is "
         "LIVE and the pop hasn't already fired before dossiering.",
)

CATALYST_FAMILY_LABEL = {
    "activist_13d": "Activist 13D value-realization campaign",
    "strategic_review": STRATEGIC_REVIEW.label,
}
CATALYST_MECHANISM = {
    "activist_13d": ("A holder has filed a Schedule 13D (>5%, non-passive) to "
                     "push for value realization — buyback, sale, spin, board "
                     "change. The campaign is the dated catalyst; Item 4 states "
                     "the intent."),
    "strategic_review": STRATEGIC_REVIEW.mechanism,
}


def sweep_by_form(
    date_from: str, date_to: str, *,
    cik_to_ticker: Optional[dict[str, str]] = None,
    exclude_ciks: Optional[set[str]] = None,
    tradable_only: bool = True,
    http_get: Callable[[str], object] = edgar.http_get,
) -> list[dict]:
    """PRIMARY hard-catalyst sourcing (100% recall by construction): enumerate
    every SC 13D / 13D-amendment in the window from EDGAR daily FORM indexes, tag
    hard_catalyst, attach a tradability flag, and by default keep only listed
    names. Every candidate carries `requires_item4_read=True` — the index cannot
    tell a campaign from a passive stake; the precision stage reads Item 4."""
    exclude = exclude_ciks or set()
    forms = [f for f, fam in CATALYST_FORM_TO_FAMILY.items() if not fss.is_graveyard(fam)]
    raw = fss.enumerate_by_form(date_from, date_to, forms, http_get=http_get)
    c2t = cik_to_ticker or {}
    out: list[dict] = []
    for cik, e in raw.items():
        if cik in exclude:
            continue
        fams = sorted({CATALYST_FORM_TO_FAMILY[f] for f in e["forms"]
                       if f in CATALYST_FORM_TO_FAMILY})
        if not fams:
            continue
        tradable = cik in c2t
        if tradable_only and not tradable:
            continue
        out.append({
            "cik": cik, "ticker": c2t.get(cik), "company": e["name"],
            "why_mispriced_type": "hard_catalyst",
            "families": fams, "family": fams[0],
            "family_label": CATALYST_FAMILY_LABEL[fams[0]],
            "mechanism": CATALYST_MECHANISM[fams[0]],
            "forms": sorted(e["forms"]),
            "first_filed": e["first"], "last_filed": e["last"],
            "n_filings": e["n"], "tradable": tradable,
            "requires_item4_read": True,   # the index can't see a campaign — Item 4 does
            "source": "form_enumeration",
        })
    # most-recent 13D first (freshest campaign = most runway before the pop)
    return sorted(out, key=lambda c: c.get("last_filed", ""), reverse=True)


def sweep_strategic_review(
    date_from: str, date_to: str, *,
    exclude_ciks: Optional[set[str]] = None,
    search_fn: Callable[..., dict] = edgar.search_filings,
) -> list[dict]:
    """Keyword supplement: 8-Ks announcing a strategic-alternatives / sale
    process (no single defining form). A supplement to the 13D spine, not a
    substitute — recall is inherently partial (prose varies)."""
    cands = fss.search_family(STRATEGIC_REVIEW, date_from, date_to, search_fn=search_fn)
    exclude = exclude_ciks or set()
    out = []
    for c in cands:
        if c["cik"] in exclude:
            continue
        c["why_mispriced_type"] = "hard_catalyst"
        c["requires_item4_read"] = False   # the 8-K states the process directly
        c["source"] = "keyword_supplement"
        out.append(c)
    return out
