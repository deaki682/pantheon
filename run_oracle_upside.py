"""Oracle upside engine — Stage 0-1 runner (field + spotlight).

Builds panel rows from the SF1 quarterly trajectory + daily marketcap already on
disk and runs oracle.upside_sourcing.screen_panel over the HUNTING GROUND. This
first run wires the BOTTOM-UP nets that the on-disk data supports — revenue
acceleration and a net-income margin-turn proxy — plus the hunting-ground gate.

HONEST COVERAGE NOTE (spec I5): relative-strength (needs a returns pull),
eps_surprise (needs an earnings feed), analyst coverage (proxied as thin — the
hunting ground is small-cap by construction), and the TOP-DOWN thematic lens
(needs a themes map) are NOT wired here yet — so this run sources on acceleration
alone and UNDER-counts (a name that is a pure thematic or pure rel-strength play
is missed this pass). The spotlight is recall-oriented and only AIMS the reader;
Stage 2 (the breadth read) is the edge and does the real work.
"""
import gzip, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import upside_sourcing as us

SF1 = "data/oracle_neglect/sf1_bs_part0.json.gz"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"

# ---- marketcap ($M -> $), latest per ticker + 6-mo momentum proxy ----------
daily = json.load(gzip.open(DAILY, "rt"))
mcap, mdate = {}, {}
series = defaultdict(dict)   # ticker -> {date: mcap_$M}
for r in daily:
    t, d = r.get("ticker"), r.get("date", "")
    if not t or r.get("marketcap") is None:
        continue
    series[t][d] = float(r["marketcap"])
    if d > mdate.get(t, ""):
        mdate[t], mcap[t] = d, float(r["marketcap"]) * 1e6
print(f"marketcap: {len(mcap)} tickers", flush=True)

# 6-mo return proxy = mcap[last]/mcap[first] - 1 (shares ~const over 6mo);
# market proxy = the cross-sectional MEDIAN return, so rel_strength = beat the median.
all_dates = sorted({d for v in series.values() for d in v})
d0, d1 = all_dates[0], all_dates[-1]
ret6 = {}
for t, v in series.items():
    if d0 in v and d1 in v and v[d0] > 0:
        ret6[t] = v[d1] / v[d0] - 1.0
_sorted = sorted(ret6.values())
median_ret = _sorted[len(_sorted) // 2] if _sorted else 0.0
print(f"6-mo momentum: {len(ret6)} tickers ({d0}->{d1}); market(median) ret={median_ret:+.1%}", flush=True)

# ---- SF1 quarterly trajectory ----------------------------------------------
byt = defaultdict(list)
for r in json.load(gzip.open(SF1, "rt")):
    if r.get("ticker"):
        byt[r["ticker"]].append(r)

panel = []
for t, rows in byt.items():
    rows.sort(key=lambda r: (r.get("calendardate") or ""))
    rev = [r.get("revenue") for r in rows if r.get("revenue") is not None]
    # net-income margin proxy per quarter (op_margin field the screen reads)
    margin = []
    for r in rows:
        rv, ni = r.get("revenue"), r.get("netinc")
        if rv and rv > 0 and ni is not None:
            margin.append(ni / rv)
    panel.append({
        "symbol": t, "mcap": mcap.get(t), "coverage": None,   # thin-coverage proxy
        "revenue": rev, "op_margin": margin,
        "ret_6m": ret6.get(t), "spy_ret_6m": median_ret,       # momentum vs the median stock
    })
print(f"panel: {len(panel)} tickers with trajectory", flush=True)

# ---- Stage 1: spotlight (bottom-up nets on disk data) ----------------------
cands = us.screen_panel(panel, forming_themes=set())   # no themes wired this run
queued = [c for c in cands if c.get("queued")]
print(f"spotlight: {len(cands)} candidates ({len(queued)} in hunting ground w/ a signal)", flush=True)

out = {"spec": "oracle_upside_stage1", "ran": "2026-07-06",
       "coverage_note": "BOTTOM-UP acceleration + margin-turn only; rel-strength/"
                        "eps/coverage/thematic NOT wired this run (under-counts).",
       "n_candidates": len(cands), "candidates": cands}
os.makedirs("cache", exist_ok=True)
json.dump(out, open("cache/oracle_upside_candidates.json", "w"), indent=1)

print("\n=== top spotlight (bottom-up) ===", flush=True)
for c in cands[:25]:
    m = (c.get("mcap") or 0) / 1e6
    print(f"  {c['symbol']:7s} score={c['spotlight_score']:5.2f} "
          f"cap=${m:6.0f}M nets={c['nets']}", flush=True)
print(f"\nwrote cache/oracle_upside_candidates.json ({len(queued)} queued for the breadth read)", flush=True)
