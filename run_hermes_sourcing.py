"""Hermes deal-sourcing runner — the COMPLETE announced-deal universe.

Replaces the session-driven "build/refresh the watchlist from news/EDGAR" step
(a sliver: whatever a run happened to surface) with an exhaustive EDGAR daily-index
sweep of the target's own merger/tender filings. Emits every announced-deal target
that filed in the trailing window, ticker-backfilled, each flagged requires_read —
the session's per-deal break-risk read then confirms cash-vs-stock, offer price,
and a live below-offer spread before any capital.

Usage:  python3 run_hermes_sourcing.py [lookback_days=120] [end_date=today]
Writes: cache/hermes_deal_universe.json  (the denominator the A/B needs to be honest)
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hermes.sourcing import sweep_deals
from shared import edgar

lookback = int(sys.argv[1]) if len(sys.argv) > 1 else 120
end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
start = end - timedelta(days=lookback)
print(f"sweeping announced-deal filings {start} -> {end} ({lookback}d)...", flush=True)

# cik10 -> ticker (invert SEC's ticker->cik master)
try:
    sym_to_cik = edgar.fetch_company_tickers()
    cik_to_sym = {c: s for s, c in sym_to_cik.items()}
except Exception as e:
    print(f"ticker map unavailable ({e!r}); candidates keep symbol=None for the read", flush=True)
    cik_to_sym = {}

cands = sweep_deals(start.isoformat(), end.isoformat(), cik_to_symbol=cik_to_sym)
n_ticker = sum(1 for c in cands if c.symbol)
print(f"announced-deal targets in window: {len(cands)}  ({n_ticker} ticker-resolved)", flush=True)

out = {
    "generated": end.isoformat(),
    "window": {"from": start.isoformat(), "to": end.isoformat(), "lookback_days": lookback},
    "n_candidates": len(cands),
    "coverage_note": (
        "COMPLETE population of announced-deal TARGETS from EDGAR daily form indexes "
        "(DEFM14A / PREM14A / DEFM14C / PREM14C / SC 14D9) — no keyword, keyed to the "
        "target CIK. KNOWN missing: (1) deals whose only public paper so far is an "
        "8-K merger agreement that has not yet drawn a proxy/14D-9 — caught on the next "
        "sweep once the proxy files; (2) acquirer-side-only tenders (SC TO-T) by design "
        "— Hermes longs the target. Cash-vs-stock is NOT decided here; every candidate "
        "requires the per-deal read."
    ),
    "candidates": [c.to_dict() for c in cands],
}
os.makedirs("cache", exist_ok=True)
json.dump(out, open("cache/hermes_deal_universe.json", "w"), indent=1)
print("wrote cache/hermes_deal_universe.json", flush=True)
print("\ntop by freshest filing:")
for c in cands[:20]:
    tk = c.symbol or "?"
    print(f"  {tk:6} {c.company[:40]:40} {'+'.join(c.forms):20} filed={c.last_filed}")
