"""Run the asset-revaluation lens on the real panel (2026-07-06).

Same data plumbing as the neglect screen (latest SF1 balance sheet + current
DAILY marketcap + TICKERS metadata), but hunts the OPPOSITE mispricing: asset-heavy
names in appreciation sectors whose cost-basis net hard assets rival the market
cap. Writes cache/oracle_asset_revaluation_candidates.json.
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import asset_revaluation as ar

NEG = "data/oracle_neglect"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"

sf1_rows = json.load(gzip.open(f"{NEG}/sf1_bs_part0.json.gz", "rt"))
sf1_by_ticker: dict[str, dict] = {}
for r in sf1_rows:
    t = r.get("ticker")
    if t and (sf1_by_ticker.get(t) is None
              or (r.get("datekey") or "") > (sf1_by_ticker[t].get("datekey") or "")):
        sf1_by_ticker[t] = r

daily = json.load(gzip.open(DAILY, "rt"))
mcap_by_ticker: dict[str, float] = {}
mdate: dict[str, str] = {}
for r in daily:
    t, d = r.get("ticker"), r.get("date", "")
    if t and r.get("marketcap") is not None and d > mdate.get(t, ""):
        mdate[t] = d
        mcap_by_ticker[t] = float(r["marketcap"]) * 1e6

raw_meta = json.load(open(f"{NEG}/tickers_meta.json"))
meta_by_ticker: dict[str, dict] = {}
for m in raw_meta:
    t = m.get("ticker")
    if not t:
        continue
    cur = m.get("currency") or "USD"
    if meta_by_ticker.get(t) is None:
        meta_by_ticker[t] = dict(m)
    elif (meta_by_ticker[t].get("currency") or "USD") == "USD" and m.get("isdelisted") == "N":
        meta_by_ticker[t] = dict(m)
    if cur != "USD":
        meta_by_ticker[t]["currency"] = cur

exclude: set[str] = set()
for path in ("cache/oracle_convex_dossiers.json",):
    if os.path.exists(path):
        try:
            data = json.load(open(path))
            for d in (data.get("dossiers", {}) or {}).values():
                if isinstance(d, dict) and d.get("symbol"):
                    exclude.add(d["symbol"].upper())
        except Exception:
            pass

cands = ar.screen_panel(sf1_by_ticker, mcap_by_ticker, meta_by_ticker, exclude_tickers=exclude)
land = [c for c in cands if c["asset_kind"] == "land"]
resource = [c for c in cands if c["asset_kind"] == "resource"]

print(f"=== {len(cands)} asset-revaluation candidates "
      f"({len(land)} land/RE/timber, {len(resource)} resource) ===", flush=True)
for c in cands[:45]:
    flag = " [commodity]" if c["commodity_dependent"] else ""
    print(f"  {c['ticker'] or '?':7s} {(c['company'] or '')[:32]:32s} {(c['industry'] or '')[:26]:26s} "
          f"cov={c['asset_coverage']:.2f}x mcap=${c['marketcap_usd']/1e6:.0f}M "
          f"nav@cost=${c['nav_at_cost_usd']/1e6:.0f}M{flag}", flush=True)
if len(cands) > 45:
    print(f"  ... +{len(cands)-45} more", flush=True)

out = {"as_of": max(mdate.values()) if mdate else None, "n": len(cands),
       "n_land": len(land), "n_resource": len(resource),
       "dials": {"coverage_min": ar.AR_COVERAGE_MIN, "leverage_max": ar.AR_LEVERAGE_MAX,
                 "cap_band": [ar.AR_MIN_CAP_USD, ar.AR_CAP_USD]},
       "candidates": cands}
json.dump(out, open("cache/oracle_asset_revaluation_candidates.json", "w"), indent=2)
print(f"\nwrote cache/oracle_asset_revaluation_candidates.json ({len(cands)} candidates)", flush=True)
