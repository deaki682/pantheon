"""Run the neglect leg on the real panel (2026-07-06).

Loads the pulled Sharadar balance-sheet panel + TICKERS metadata + current DAILY
marketcaps, keeps the LATEST balance sheet per ticker, converts marketcap from
Sharadar's $M to dollars, and runs `oracle.neglect_screen.screen_panel`. Writes
the below-floor candidates to cache/oracle_neglect_candidates.json — the coverage
output that feeds the dossier→verify precision gate.
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import neglect_screen as ns

NEG = "data/oracle_neglect"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"

# ---- latest SF1 balance sheet per ticker -----------------------------------
sf1_rows = json.load(gzip.open(f"{NEG}/sf1_bs_part0.json.gz", "rt"))
sf1_by_ticker: dict[str, dict] = {}
for r in sf1_rows:
    t = r.get("ticker")
    if not t:
        continue
    prev = sf1_by_ticker.get(t)
    if prev is None or (r.get("datekey") or "") > (prev.get("datekey") or ""):
        sf1_by_ticker[t] = r
print(f"latest SF1 balance sheet for {len(sf1_by_ticker)} tickers", flush=True)

# ---- current marketcap ($M -> $) -------------------------------------------
daily = json.load(gzip.open(DAILY, "rt"))
mcap_by_ticker: dict[str, float] = {}
mcap_date: dict[str, str] = {}
for r in daily:
    t, d = r.get("ticker"), r.get("date", "")
    if not t or r.get("marketcap") is None:
        continue
    if d > mcap_date.get(t, ""):
        mcap_date[t] = d
        mcap_by_ticker[t] = float(r["marketcap"]) * 1e6   # $M -> $
print(f"current marketcap for {len(mcap_by_ticker)} tickers "
      f"(latest {max(mcap_date.values()) if mcap_date else '?'})", flush=True)

# ---- TICKERS metadata ------------------------------------------------------
# Sharadar has multiple rows per ticker (recycled tickers, dual-currency ADRs).
# GRVY has a KRW row AND a USD row; a naive dict keeps the last and lets the
# KRW-reporting balance sheet through against a USD marketcap (the FX artifact).
# Collapse conservatively: if ANY row for a ticker is non-USD, we can't be sure
# which currency the SF1 is in, so stamp the row non-USD (the screen drops it).
_raw_meta = json.load(open(f"{NEG}/tickers_meta.json"))
meta_by_ticker: dict[str, dict] = {}
for m in _raw_meta:
    t = m.get("ticker")
    if not t:
        continue
    cur = m.get("currency") or "USD"
    prev = meta_by_ticker.get(t)
    if prev is None:
        meta_by_ticker[t] = dict(m)
    else:
        # prefer a live common-stock row for display; but a non-USD row anywhere
        # forces the ticker non-USD (ambiguous currency -> not screenable)
        if (prev.get("currency") or "USD") == "USD" and m.get("isdelisted") == "N":
            meta_by_ticker[t] = dict(m)
        if cur != "USD":
            meta_by_ticker[t]["currency"] = cur
print(f"metadata for {len(meta_by_ticker)} tickers "
      f"({sum(1 for v in meta_by_ticker.values() if (v.get('currency') or 'USD')!='USD')} non-USD)", flush=True)

# ---- exclude names already in the pool / legacy cohort ---------------------
exclude: set[str] = set()
for path in ("cache/oracle_convex_dossiers.json", "cache/oracle_dossiers.json"):
    if os.path.exists(path):
        try:
            data = json.load(open(path))
            items = data.values() if isinstance(data, dict) else data
            for d in items:
                if isinstance(d, dict) and d.get("symbol"):
                    exclude.add(d["symbol"].upper())
        except Exception:
            pass
if exclude:
    print(f"excluding {len(exclude)} names already in the pool: {sorted(exclude)}", flush=True)

# ---- screen ----------------------------------------------------------------
cands = ns.screen_panel(sf1_by_ticker, mcap_by_ticker, meta_by_ticker,
                        exclude_tickers=exclude)

by_type: dict[str, int] = {}
for c in cands:
    by_type[c["floor_type"]] = by_type.get(c["floor_type"], 0) + 1

print(f"\n=== {len(cands)} below-floor NEGLECT candidates "
      f"({by_type}) ===", flush=True)
for c in cands[:60]:
    flag = " ERODING" if c["eroding_floor"] else ""
    rw = f" runway={c['runway_quarters']}q" if c["runway_quarters"] is not None else ""
    print(f"  {c['ticker'] or '?':7s} {(c['company'] or '')[:34]:34s} "
          f"{c['floor_type']:13s} disc={c['discount']:+.0%}  "
          f"mcap=${c['marketcap_usd']/1e6:.0f}M floor=${c['floor_usd']/1e6:.0f}M"
          f"{rw}{flag}", flush=True)
if len(cands) > 60:
    print(f"  ... +{len(cands)-60} more", flush=True)

out = {"screened": len(sf1_by_ticker), "as_of": max(mcap_date.values()) if mcap_date else None,
       "n_candidates": len(cands), "by_floor_type": by_type,
       "dials": {"neglect_cap_usd": ns.NEGLECT_CAP_USD, "min_cap_usd": ns.MIN_CAP_USD,
                 "min_runway_q": ns.MIN_RUNWAY_Q},
       "candidates": cands}
json.dump(out, open("cache/oracle_neglect_candidates.json", "w"), indent=2)
print(f"\nwrote cache/oracle_neglect_candidates.json ({len(cands)} candidates)", flush=True)
