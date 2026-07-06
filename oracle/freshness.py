"""Freshness reconciliation — cross-check the Sharadar screen against a live
broker feed (2026-07-06).

The neglect / asset-revaluation screens compute the discount off Sharadar's DAILY
marketcap, which uses Sharadar's share count — and that count LAGS post-quarter
conversions, reverse splits, and big raises. FTH broke exactly here: Sharadar
carried 1.34M shares ($31M cap → a phantom "85% below net cash"), while the true
post-conversion count was 25.78M ($590M cap → ABOVE net cash). A live broker
(Robinhood) fundamentals feed has the CURRENT share count, so cross-referencing
its market cap turns the #1 precision-only trap (stale share count) into a
screen-stage catch.

This module is the PURE reconciliation logic (no network — the caller fetches the
broker fundamentals and passes them in, because the broker feed is an
MCP/credentialed call, not importable here). `robin_stocks` is absent in this
environment, so `shared.broker` returns nothing from a script; the live feed comes
via the assistant's MCP `get_equity_fundamentals` and is handed to
`apply_reconciliation` as {ticker: market_cap}.

A live share count catches stale-COMMON-count changes (conversions/splits/raises).
It does NOT include as-converted preferred or in-the-money warrants (INVE's 7.13M
preferred) — that fully-diluted haircut is still a 10-Q job. So this closes the
stale-count hole, not the dilution-overhang hole; both matter, this fixes the one
a live feed can.
"""
from __future__ import annotations

from typing import Optional

# A live-vs-Sharadar marketcap gap this large means the share count moved
# materially (conversion / split / raise) since Sharadar's snapshot — trust the
# live feed and flag it.
DIVERGENCE_FLAG = 0.20
# A below-cash / below-book thesis needs a book value that EXISTS and isn't tiny:
# 0 < P/B < ~this. P/B <= 0 means NEGATIVE book (no floor — the MNRO/FTH shape);
# P/B >= this means the "floor" is a data/currency artifact (LAWR reported yen -> a
# phantom "net cash" while trading at 119x book). Either contradicts the floor.
PB_ARTIFACT_HIGH = 3.0
# Crypto-treasury markers in the broker's DESCRIPTION — catches the shells whose
# NAME hides the pivot (AVX "AVAX One", BNC "CEA Industries"/BNB, NAKA "Nakamoto",
# AIFC "AI Financial", SKYA "SkyAI"/stablecoin) — their "cash/investments" floor is
# a volatile coin pile, not hard cash.
CRYPTO_DESC_MARKERS = (
    "bitcoin", "digital asset", "crypto", "blockchain", "stablecoin", "onchain",
    "avax", "avalanche", "ethereum", "zcash", " bnb ", "web3", "token treasury",
    "digital-asset", "treasury strategy",
)


def reconcile_marketcap(
    cand: dict, rh_market_cap: Optional[float], *, divergence_flag: float = DIVERGENCE_FLAG
) -> dict:
    """Return a copy of the candidate with its marketcap reconciled to the live
    broker feed. When the live cap is available it REPLACES the Sharadar cap
    (fresher), the discount-to-floor is recomputed, `below_floor` is set, and
    `stale_marketcap` flags a divergence past the threshold. When the live cap is
    missing, the Sharadar values are kept untouched."""
    out = dict(cand)
    shar = cand.get("marketcap_usd")
    floor = cand.get("floor_usd") or cand.get("nav_at_cost_usd") or 0
    if not rh_market_cap or rh_market_cap <= 0 or not shar or shar <= 0:
        out["marketcap_source"] = "sharadar"
        out["stale_marketcap"] = False
        out.setdefault("below_floor", True)   # it passed the screen on Sharadar
        return out
    div = abs(rh_market_cap - shar) / shar
    out["sharadar_marketcap_usd"] = shar
    out["marketcap_usd"] = round(float(rh_market_cap), 0)
    out["marketcap_source"] = "robinhood"
    out["marketcap_divergence"] = round(div, 2)
    out["stale_marketcap"] = div >= divergence_flag
    if floor > 0:
        out["discount"] = round(1.0 - rh_market_cap / floor, 4)
        out["below_floor"] = rh_market_cap < floor
    else:
        out.setdefault("below_floor", True)
    return out


def reconcile_with_fundamentals(
    cand: dict, rh_row: Optional[dict], *, divergence_flag: float = DIVERGENCE_FLAG,
    pb_high: float = PB_ARTIFACT_HIGH,
) -> dict:
    """Full broker cross-check: reconcile the marketcap AND add two more flags the
    live fundamentals feed makes cheap — `book_contradicts_floor` (P/B <= 0 or
    >= pb_high, i.e. no book or a currency/data artifact) and `crypto_treasury`
    (the description reveals a coin pile the name hides). `rh_row` is a broker
    get_equity_fundamentals row (market_cap, pb_ratio, description)."""
    mc = None
    if rh_row:
        try:
            mc = float(rh_row.get("market_cap")) if rh_row.get("market_cap") is not None else None
        except (TypeError, ValueError):
            mc = None
    out = reconcile_marketcap(cand, mc, divergence_flag=divergence_flag)
    if rh_row:
        try:
            pb = float(rh_row.get("pb_ratio")) if rh_row.get("pb_ratio") is not None else None
        except (TypeError, ValueError):
            pb = None
        out["rh_pb_ratio"] = pb
        out["book_contradicts_floor"] = pb is not None and (pb <= 0 or pb >= pb_high)
        desc = (rh_row.get("description") or "").lower()
        out["crypto_treasury"] = any(m in desc for m in CRYPTO_DESC_MARKERS)
    return out


def is_clean(cand: dict) -> bool:
    """A candidate is clean only if reconciliation ACTUALLY RAN against a live feed
    (marketcap_source stamped) AND the fresh cap still leaves it below its floor AND
    neither the book-contradiction nor the crypto-treasury flag fired.

    FAIL-CLOSED (2026-07-06 audit fix): an UN-reconciled candidate (no
    marketcap_source) returns False, not True — otherwise this gate passes every
    raw candidate the moment reconciliation is skipped (which is exactly how the
    live pipeline shipped: reconciliation was never called, so is_clean rubber-
    stamped everything). The floor/crypto/book flags only exist after a reconcile;
    absent them, the honest answer is 'not verified clean', not 'clean'."""
    if not cand.get("marketcap_source"):
        return False
    return bool(cand.get("below_floor", False)
                and not cand.get("book_contradicts_floor")
                and not cand.get("crypto_treasury"))


def apply_full_reconciliation(
    candidates: list[dict], rh_row_by_ticker: dict[str, dict], *,
    divergence_flag: float = DIVERGENCE_FLAG, drop_unclean: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Reconcile a candidate list against a live {ticker: get_equity_fundamentals
    row} feed, running the FULL check (marketcap + book-contradiction + crypto),
    not just the marketcap (the audit found apply_reconciliation silently ran only
    1 of the 3 advertised checks). Returns (kept, dropped): a name is dropped when
    the fresh cap pushes it above its floor, its book contradicts the floor, or it
    is a crypto treasury. `kept` is re-sorted by reconciled discount, deepest first.
    A ticker missing from the feed is reconciled marketcap-only and, under
    drop_unclean, dropped as not-clean (fail-closed — we could not confirm it)."""
    kept, dropped = [], []
    for c in candidates:
        rc = reconcile_with_fundamentals(c, rh_row_by_ticker.get(c.get("ticker")),
                                         divergence_flag=divergence_flag)
        if drop_unclean and not is_clean(rc):
            rc.setdefault("dropped_reason",
                          "freshness: not below floor / book-contradiction / crypto / unreconciled")
            dropped.append(rc)
        else:
            kept.append(rc)
    kept.sort(key=lambda c: -(c.get("discount") or -9))
    return kept, dropped


def apply_reconciliation(
    candidates: list[dict], rh_market_cap_by_ticker: dict[str, float], *,
    divergence_flag: float = DIVERGENCE_FLAG, drop_above_floor: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Reconcile a candidate list against a live {ticker: market_cap} feed.

    Returns (kept, dropped). A name whose FRESH market cap pushes it back ABOVE its
    floor (the FTH case) is moved to `dropped` when drop_above_floor — it was never
    really below the floor, the Sharadar cap was stale. `kept` is re-sorted by the
    reconciled discount, deepest first."""
    kept, dropped = [], []
    for c in candidates:
        rc = reconcile_marketcap(c, rh_market_cap_by_ticker.get(c.get("ticker")),
                                 divergence_flag=divergence_flag)
        if drop_above_floor and rc.get("below_floor") is False:
            rc["dropped_reason"] = ("fresh broker marketcap is ABOVE the floor — "
                                    "the Sharadar cap was stale (share-count lag)")
            dropped.append(rc)
        else:
            kept.append(rc)
    kept.sort(key=lambda c: -(c.get("discount") or -9))
    return kept, dropped
