"""Oracle upside engine — Stage 0-1 runner: the SYSTEMATIC best-first ranker.

Pass 1 of the machine (oracle.upside_ranker.rank_all): compose EVERY data-fed net
over the WHOLE universe and rank best-first. No hand-picking, no sliver — every
in-ground name is ranked or recorded as dropped-with-reason, and a coverage report
states exactly what ran and what is KNOWN missing.

Nets active on this on-disk pass: acceleration (SF1 revenue/margin trajectory),
recent_strength (daily-marketcap ~5wk trend), value_floor (SF1 tangible-book /
net-cash vs marketcap). Nets that activate on the LIVE-verified top slice
(assistant pulls Robinhood, runs upside_ranker.reconcile_top): range_reversal
(true 52wk range), earnings_surprise (get_earnings_results). Nets still needing a
feed (logged INACTIVE, wiring is the follow-on): thematic (a forming-themes map),
special_situation (EDGAR spinoff/IPO/reorg events).

Emits cache/oracle_upside_candidates.json (full ranking + coverage) and prints the
top-N symbol batches for the assistant's live-verify pull.
"""
import gzip, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import upside_ranker as ur

SF1 = "data/oracle_neglect/sf1_bs_part0.json.gz"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"
META = "data/oracle_neglect/tickers_meta.json"
LEGACY = {"CXT", "HDSN", "J", "PSN", "VITL"}     # frozen legacy cohort — never the engine's
TOP_N_VERIFY = 250                                # how deep the live-verify slice goes

# ---- ticker meta: sector (exclude financials — value_floor loves cheap banks/
# REITs but they aren't inflection names) + FX/reachability guard (USD reporters,
# no China/HK VIEs) + real sector tags for the candidates ---------------------
_meta_raw = json.load(open(META))
meta = {}
for m in _meta_raw:
    t = m.get("ticker")
    if not t:
        continue
    if t not in meta or (m.get("isdelisted") == "N" and meta[t].get("isdelisted") != "N"):
        meta[t] = m
EXCLUDE_SECTORS = {"Financial Services", "Real Estate"}   # not inflection hunting ground
EXCLUDE_LOCATIONS = {"China", "Hong Kong"}                # unreachable / VIE risk


def meta_ok(t: str) -> bool:
    m = meta.get(t)
    if not m:
        return True                                        # unknown -> keep, live-verify catches it
    if (m.get("currency") or "USD") != "USD":
        return False
    if m.get("sector") in EXCLUDE_SECTORS:
        return False
    if (m.get("location") or "") in EXCLUDE_LOCATIONS:
        return False
    return True

# ---- current marketcap + recent (~5wk) trend -------------------------------
daily = json.load(gzip.open(DAILY, "rt"))
series = defaultdict(dict)
for r in daily:
    if r.get("ticker") and r.get("marketcap") is not None:
        series[r["ticker"]][r.get("date", "")] = float(r["marketcap"])
all_dates = sorted({d for v in series.values() for d in v})
d0, d1 = all_dates[0], all_dates[-1]
d_recent = all_dates[-25] if len(all_dates) >= 25 else all_dates[0]
mcap, ret_recent = {}, {}
for t, v in series.items():
    if d1 in v and v[d1] > 0:
        mcap[t] = v[d1] * 1e6
        if d_recent in v and v[d_recent] > 0:
            ret_recent[t] = v[d1] / v[d_recent] - 1.0
_sr = sorted(ret_recent.values())
median_recent = _sr[len(_sr) // 2] if _sr else 0.0
print(f"marketcap {len(mcap)} | recent-trend {len(ret_recent)} ({d_recent}->{d1}); median {median_recent:+.1%}", flush=True)

# ---- SF1: latest balance sheet + revenue/margin trajectory -----------------
byt = defaultdict(list)
for r in json.load(gzip.open(SF1, "rt")):
    if r.get("ticker"):
        byt[r["ticker"]].append(r)

panel, n_valuefloor, n_excluded = [], 0, 0
for t, rows in byt.items():
    if t in LEGACY:
        continue
    if not meta_ok(t):                       # financials / REITs / non-USD / China excluded
        n_excluded += 1
        continue
    rows.sort(key=lambda r: (r.get("calendardate") or ""))
    rev = [r.get("revenue") for r in rows if r.get("revenue") is not None]
    margin = [r["netinc"] / r["revenue"] for r in rows
              if r.get("revenue") and r["revenue"] > 0 and r.get("netinc") is not None]
    latest = rows[-1]
    mc = mcap.get(t)
    row = {"symbol": t, "mcap": mc, "coverage": None,
           "sector": (meta.get(t) or {}).get("sector"),
           "revenue": rev, "op_margin": margin,
           "ret_recent": ret_recent.get(t), "spy_ret_recent": median_recent}
    # value_floor inputs from the latest balance sheet (SF1)
    if mc and mc > 0:
        eq, intang = latest.get("equity"), latest.get("intangibles") or 0.0
        cash = (latest.get("cashneq") or 0.0) + (latest.get("investmentsc") or 0.0)
        debt = latest.get("debt") or 0.0
        if eq is not None:
            tb = float(eq) - float(intang)
            if tb > 0:
                row["price_to_tangible_book"] = mc / tb
        row["net_cash_ratio"] = (cash - debt) / mc
        n_valuefloor += 1
    panel.append(row)
print(f"panel {len(panel)} tickers ({n_valuefloor} with value_floor inputs; "
      f"{n_excluded} excluded: financials/REITs/non-USD/China)", flush=True)

# ---- pass 1: systematic best-first ranking over the WHOLE universe ----------
out = ur.rank_all(panel, themes=set())     # thematic net inactive (no themes map yet)
ranked, cov = out["ranked"], out["coverage"]

# coverage_note: what ran, what is KNOWN missing (spec I5 / populations discipline)
cov["known_missing"] = [
    "universe = 5,593 SF1 filers on disk; ~20% of US-listed (recent IPOs, thin-filers, "
    "many ADRs) NOT in the panel — needs a full-universe pull",
    "earnings_surprise net: activates on the live-verify slice (Robinhood get_earnings_results)",
    "thematic net: INACTIVE — needs a maintained forming-themes map + business tagging",
    "special_situation net: INACTIVE — needs EDGAR spinoff/IPO/reorg events (forced_seller_sourcing)",
]
json.dump({"spec": "oracle_upside_rank_all", "ran": "2026-07-06",
           "coverage": cov, "n_ranked": len(ranked), "ranked": ranked},
          open("cache/oracle_upside_candidates.json", "w"), indent=1)

print(f"\n=== COVERAGE ===\n  panel={cov['n_panel']}  ranked={cov['n_ranked']}  "
      f"dropped={cov['dropped']}\n  active_nets={cov['active_nets']}\n  inactive_nets={cov['inactive_nets']}", flush=True)
print("\n=== top 20 (whole-universe composite, pre-live-verify) ===", flush=True)
for c in ranked[:20]:
    print(f"  #{c['rank']:<3} {c['symbol']:6} comp={c['composite']:5.2f} "
          f"nets={ {k: round(v,2) for k,v in c['nets'].items()} }", flush=True)

print(f"\n=== TOP {TOP_N_VERIFY} SYMBOLS FOR LIVE VERIFY (batches of 10) ===", flush=True)
top = [c["symbol"] for c in ranked[:TOP_N_VERIFY]]
for i in range(0, len(top), 10):
    print(json.dumps(top[i:i+10]), flush=True)
print(f"\nwrote cache/oracle_upside_candidates.json ({len(ranked)} ranked; top {len(top)} queued for live verify)", flush=True)
