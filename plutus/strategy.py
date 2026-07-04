"""Plutus's frozen strategy: net-issuance-low N50 LARGE (gauntlet_v2).

THE canonical implementation of the validated basket. Both Plutus's live
runbook and the paper forward test (run_forward_net_issuance.py) import from
here, so the live book and the tracked forward test can never drift apart —
they are, by construction, the same 50 names.

Convention (frozen, matches the validated backtest verbatim):
  - signal date D = a calendar quarter-end
  - universe = top 500 US names by Sharadar DAILY marketcap on/near D
  - metric  = trailing-4Q vs prior-4Q change in weighted average shares
              (SF1 ARQ ``shareswa``, using only filings with datekey <= D so
              it is strictly point-in-time — no look-ahead)
  - hold    = the 50 names with the LOWEST (most negative) share-count change
  - weight  = equal (~2%/name)

This module computes only the SIGNAL (which names). Execution prices come
from the live broker tape in the runbook; the forward test supplies its own
Sharadar closeadj for grading. Survivorship: SEP/SF1/DAILY are the
survivorship-bias-free Sharadar panels (delisted names retained), so the
basket is honest about names that later died — see shared/sharadar.py.
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import date, timedelta

import shared.sharadar as sh

UNIVERSE_SIZE = 500
BASKET_SIZE = 50
LOOKBACK_Q = 8          # 8 quarters: trailing-4Q sum vs prior-4Q sum
STALE_FILING_DAYS = 400  # drop names whose latest filing is >400d before D


def _datatable(table, **kw):
    """Sharadar call with the same 4-try exponential backoff the pull/forward
    scripts use — the SEP/SF1/DAILY endpoints occasionally 5xx."""
    for a in range(4):
        try:
            return sh._datatable(table, **kw)
        except Exception:
            if a == 3:
                raise
            time.sleep(2 ** (a + 1))


def top_universe(D: str, size: int = UNIVERSE_SIZE) -> set:
    """Top `size` tickers by DAILY marketcap on/near quarter-end D."""
    rows = None
    for off in range(6):
        dd = (date(*map(int, D.split("-"))) - timedelta(days=off)).isoformat()
        rows = _datatable("DAILY", **{"date.gte": dd, "date.lte": dd,
                          "qopts.columns": "ticker,marketcap", "qopts.per_page": 10000})
        if rows:
            break
    m = {r["ticker"].upper(): r["marketcap"] for r in (rows or []) if r.get("marketcap")}
    return set(sorted(m, key=lambda t: -m[t])[:size])


def net_issuance_basket(D: str, universe: set, size: int = BASKET_SIZE) -> list:
    """The `size` lowest trailing-net-issuance names in `universe` as of D.

    Point-in-time: only SF1 rows with datekey <= D are used, so the basket is
    computable on D with no future filings. Names with <8 usable quarters or a
    stale latest filing are dropped (disclosed by the shorter returned list).
    """
    syms = sorted(universe)
    rows = []
    for i in range(0, len(syms), 90):
        rows += _datatable("SF1", ticker=",".join(syms[i:i + 90]), dimension="ARQ", **{
            "calendardate.gte": "2023-01-01",
            "qopts.columns": "ticker,datekey,calendardate,shareswa",
            "qopts.per_page": 10000})
    byt = defaultdict(list)
    for r in rows:
        if r.get("shareswa") is not None:
            byt[r["ticker"]].append(r)
    for t in byt:
        byt[t].sort(key=lambda r: (r["calendardate"], r["datekey"]))
    stale_before = (date(*map(int, D.split("-"))) - timedelta(days=STALE_FILING_DAYS)).isoformat()
    cand = []
    for t in universe:
        u = [r for r in byt.get(t, []) if r["datekey"] <= D]
        if len(u) < LOOKBACK_Q:
            continue
        l8 = u[-LOOKBACK_Q:]
        if l8[-1]["calendardate"] < stale_before:
            continue  # latest filing too old — name has gone quiet
        recent = sum(r["shareswa"] for r in l8[4:])   # trailing 4Q
        prior = sum(r["shareswa"] for r in l8[:4])    # prior 4Q
        if prior > 0:
            cand.append((recent / prior - 1.0, t))    # share-count change
    cand.sort()                                       # most-negative first
    return [t for _, t in cand[:size]]


def quarterly_basket(D: str) -> list:
    """The full frozen pick for quarter-end D: top-500 universe → 50 lowest
    net-issuance names. This is exactly what Plutus holds for the quarter."""
    return net_issuance_basket(D, top_universe(D))


# ---- calendar helpers (Date.now() is blocked in some envs; callers pass dates) ----

_Q_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


def latest_data_date() -> str:
    """Most recent SEP bar date — the honest 'today' for a data-driven session
    when the wall clock isn't trustworthy. Probes a always-present ticker."""
    probe = _datatable("SEP", ticker="AAPL", **{"date.gte": "2026-01-01",
                       "qopts.columns": "ticker,date", "qopts.per_page": 10000})
    return max(r["date"][:10] for r in probe)


def quarter_end_on_or_before(today: str) -> str:
    """The most recent calendar quarter-end <= today (the current signal date)."""
    y = int(today[:4])
    best = f"{y - 1}-12-31"
    for m, d in _Q_ENDS:
        qe = f"{y}-{m:02d}-{d:02d}"
        if qe <= today:
            best = qe
    return best


def quarter_label(qe: str) -> str:
    return f"{qe[:4]}Q{(int(qe[5:7]) - 1) // 3 + 1}"


def next_quarter_end(qe: str) -> str:
    qi = (int(qe[5:7]) - 1) // 3
    nq = _Q_ENDS[(qi + 1) % 4]
    ny = int(qe[:4]) + (1 if qi == 3 else 0)
    return f"{ny}-{nq[0]:02d}-{nq[1]:02d}"
