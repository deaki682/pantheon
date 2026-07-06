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

# RECENT-trend momentum (2026-07-06 fix) — NOT 6mo trailing (which surfaced faded
# spikes). recent = last ~25 trading days (~5wk). Also distance below the window
# high (pct_below_high) to penalize already-arrived names near their high.
all_dates = sorted({d for v in series.values() for d in v})
d0, d1 = all_dates[0], all_dates[-1]
d_recent = all_dates[-25] if len(all_dates) >= 25 else all_dates[0]
ret_recent, pct_below_high = {}, {}
for t, v in series.items():
    if d1 not in v or v[d1] <= 0:
        continue
    if d_recent in v and v[d_recent] > 0:
        ret_recent[t] = v[d1] / v[d_recent] - 1.0
    hi = max(v.values())
    if hi > 0:
        pct_below_high[t] = 1.0 - v[d1] / hi
_sorted = sorted(ret_recent.values())
median_recent = _sorted[len(_sorted) // 2] if _sorted else 0.0
print(f"recent momentum: {len(ret_recent)} tickers ({d_recent}->{d1}, ~5wk); "
      f"market(median) recent ret={median_recent:+.1%}", flush=True)

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
        "ret_recent": ret_recent.get(t), "spy_ret_recent": median_recent,  # RECENT trend vs median
        "pct_below_high": pct_below_high.get(t),               # distance below the window high
    })
print(f"panel: {len(panel)} tickers with trajectory", flush=True)

# ---- Stage 1: spotlight (bottom-up nets on disk data) ----------------------
# Skip the FROZEN legacy cohort — not the engine's to trade (operator directive).
LEGACY = {"CXT", "HDSN", "J", "PSN", "VITL"}
panel = [r for r in panel if r["symbol"] not in LEGACY]
cands = us.screen_panel(panel, forming_themes=set())   # no themes wired this run
queued = [c for c in cands if c.get("queued")]
print(f"spotlight: {len(cands)} candidates ({len(queued)} in hunting ground w/ a signal)", flush=True)

out = {"spec": "oracle_upside_stage1", "ran": "2026-07-06",
       "coverage_note": "BOTTOM-UP acceleration + margin-turn only; rel-strength/"
                        "eps/coverage/thematic NOT wired this run (under-counts).",
       "n_candidates": len(cands), "candidates": cands}
os.makedirs("cache", exist_ok=True)
json.dump(out, open("cache/oracle_upside_candidates.json", "w"), indent=1)

print("\n=== top spotlight (recent-trend, arrival-penalized) ===", flush=True)
for c in cands[:25]:
    m = (c.get("mcap") or 0) / 1e6
    pbh = c.get("pct_below_high")
    rr = c.get("ret_recent")
    print(f"  {c['symbol']:7s} score={c['spotlight_score']:5.2f} cap=${m:6.0f}M "
          f"recent={ (rr*100 if rr is not None else 0):+5.0f}% "
          f"belowHigh={ (pbh*100 if pbh is not None else 0):3.0f}% nets={c['nets']}", flush=True)
print(f"\nwrote cache/oracle_upside_candidates.json ({len(queued)} queued for the breadth read)", flush=True)
