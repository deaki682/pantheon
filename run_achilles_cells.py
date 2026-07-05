"""achilles_pead_gauntlet phase 5: join prices onto events and run the 18 cells.

Timeline per event (the look-ahead guard, prereg-faithful):
  i0   = last trading bar STRICTLY BEFORE datekey  (pre-report close)
  i0+1 = report bar, i0+2 = reaction bar           (reaction = ca[i0+2]/ca[i0]-1)
  i0+3 = ENTRY bar (the day AFTER the reaction bar; entry at its close)
Entry never touches a close used to measure the reaction. Stops use the
ADJUSTED low (low * closeadj/close). A series that ends mid-hold (delisting)
EXITS AT THE LAST PRINT and the trade is KEPT (reason 'delist') — dropping it
would be survivorship bias. SUE threshold = 80th pct of IN-SAMPLE events only.
Benchmark = the event's own bucket's equal-weight over the identical window.
Costs one-way: SMALL 30bps, MICRO 60bps; the 2x stress doubles them.
PAPER ONLY. docs/lab_prereg_achilles_pead_gauntlet.md.
"""
import gzip, json, os, sys, bisect, math
from array import array
from collections import defaultdict

OUT = "data/achilles_gauntlet"
HOLDS = (5, 10, 20)
CAPS = (("none", 1e9), ("cap20", 0.20), ("cap10", 0.10))
BUCKETS = ("SMALL", "MICRO")
COST_ONEWAY = {"SMALL": 0.0030, "MICRO": 0.0060}
STOP_PCT = 0.08
IN_SAMPLE_END = "2015-12-31"   # entry-date split; holdout 2016+ touched once

def d2i(s): return int(s[:4]) * 10000 + int(s[5:7]) * 100 + int(s[8:10])

# ---------- 1. load SEP into compact per-ticker arrays ----------
print("loading SEP...", flush=True)
px = {}   # ticker -> (dates:array('i'), ca:array('f'), lowadj:array('f'), openadj:array('f'))
tmp = defaultdict(lambda: [array('i'), array('f'), array('f'), array('f')])
for part in sorted(os.listdir(OUT)):
    if not part.startswith("sep_part"):
        continue
    for r in json.load(gzip.open(f"{OUT}/{part}", "rt")):
        c, ca, lo, op = r.get("close"), r.get("closeadj"), r.get("low"), r.get("open")
        if not c or not ca or ca <= 0 or c <= 0:
            continue
        t = tmp[r["ticker"]]
        adj = ca / c
        t[0].append(d2i(r["date"]))
        t[1].append(ca)
        t[2].append((lo if lo and lo > 0 else c) * adj)   # adjusted low
        t[3].append((op if op and op > 0 else c) * adj)   # adjusted open (gap-fill)
print(f"  {sum(len(v[0]) for v in tmp.values())} bars, {len(tmp)} tickers", flush=True)
for tkr, (ds, cas, los, ops) in tmp.items():
    order = sorted(range(len(ds)), key=lambda i: ds[i])
    px[tkr] = (array('i', (ds[i] for i in order)),
               array('f', (cas[i] for i in order)),
               array('f', (los[i] for i in order)),
               array('f', (ops[i] for i in order)))
del tmp

# ---------- 2. bucket EW daily index ----------
print("building bucket EW indexes...", flush=True)
U = json.load(open(f"{OUT}/universes.json"))["universes"]
acc = {b: defaultdict(lambda: [0.0, 0]) for b in BUCKETS}   # dateint -> [sum, n]
for snap_date in sorted(U):
    ym = snap_date[:7]
    y, m = int(ym[:4]), int(ym[5:7])
    m2, y2 = (m + 1, y) if m < 12 else (1, y + 1)
    lo_i, hi_i = (y2 * 10000 + m2 * 100 + 1), (y2 * 10000 + m2 * 100 + 31)  # NEXT month (PIT: snapshot trades the following month)
    for b in BUCKETS:
        a = acc[b]
        for tkr in U[snap_date][b]:
            p = px.get(tkr)
            if p is None:
                continue
            ds, cas = p[0], p[1]
            j0 = bisect.bisect_left(ds, lo_i)
            j1 = bisect.bisect_right(ds, hi_i)
            for j in range(max(j0, 1), j1):
                r = cas[j] / cas[j - 1] - 1.0
                cell = a[ds[j]]
                cell[0] += r
                cell[1] += 1
ew_cum, ew_dates = {}, {}
for b in BUCKETS:
    days = sorted(acc[b])
    cum = array('d', [1.0] * (len(days) + 1))
    for k, d in enumerate(days):
        s, n = acc[b][d]
        cum[k + 1] = cum[k] * (1.0 + (s / n if n else 0.0))
    ew_dates[b], ew_cum[b] = days, cum
del acc
print("  EW days:", {b: len(ew_dates[b]) for b in BUCKETS}, flush=True)

def bench_ret(bucket, entry_di, exit_di):
    days, cum = ew_dates[bucket], ew_cum[bucket]
    k0 = bisect.bisect_right(days, entry_di)   # first EW day AFTER entry
    k1 = bisect.bisect_right(days, exit_di)    # through exit day inclusive
    if k1 <= k0:
        return 0.0
    return cum[k1] / cum[k0] - 1.0

# ---------- 3. per-event trades (reaction + one sim per hold) ----------
print("simulating events...", flush=True)
events = json.load(open(f"{OUT}/events.json"))
trades = []      # rows: dict with sue, bucket, entry_date, reaction, per-hold results
skipped = {"no_px": 0, "short_series": 0}
for ev in events:
    p = px.get(ev["symbol"])
    if p is None:
        skipped["no_px"] += 1
        continue
    ds, cas, los, ops = p
    dk = d2i(ev["datekey"])
    i0 = bisect.bisect_left(ds, dk) - 1        # last bar STRICTLY before datekey
    ie = i0 + 3                                 # entry bar
    if i0 < 0 or ie >= len(ds):
        skipped["short_series"] += 1
        continue
    reaction = cas[i0 + 2] / cas[i0] - 1.0
    entry = cas[ie]
    if entry <= 0:
        skipped["short_series"] += 1
        continue
    stop = entry * (1.0 - STOP_PCT)
    row = {"sue": ev["sue"], "bucket": ev["bucket"], "reaction": reaction,
           "entry_date": ev["datekey"], "entry_di": ds[ie]}
    for H in HOLDS:
        gross, reason, exit_di = None, "time", None
        last = min(ie + H, len(ds) - 1)
        for j in range(ie + 1, last + 1):
            if los[j] <= stop:
                # gap-through fill (bug-hunt 2026-07-05): if the bar OPENS at/
                # below the stop, the fill is the open, not the stop level
                fill = ops[j] if ops[j] <= stop else stop
                gross, reason, exit_di = fill / entry - 1.0, "stop", ds[j]
                break
        if gross is None:
            exit_di = ds[last]
            gross = cas[last] / entry - 1.0
            if last < ie + H:
                reason = "delist"
        row[f"h{H}"] = (gross, reason, exit_di)
    trades.append(row)
print(f"  {len(trades)} events priced | skipped {skipped}", flush=True)

# ---------- 4. SUE threshold from IN-SAMPLE only ----------
ins = sorted(t["sue"] for t in trades if t["entry_date"] <= IN_SAMPLE_END)
thr = ins[int(0.80 * len(ins))]
print(f"  SUE 80th pct (in-sample only) = {thr:.3f}", flush=True)

# ---------- 5. the 18 cells ----------
def stats(xs):
    n = len(xs)
    if n < 2:
        return {"n": n}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": round(m, 5),
            "t": round(m / (sd / math.sqrt(n)), 2) if sd > 0 else None,
            "win": round(sum(1 for x in xs if x > 0) / n, 3)}

results = {}
for b in BUCKETS:
    for H in HOLDS:
        for cap_name, cap in CAPS:
            key = f"{b}_h{H}_{cap_name}"
            cell = {"in_sample": {}, "holdout": {}}
            for window, lo_d, hi_d in (("in_sample", "0000-00-00", IN_SAMPLE_END),
                                       ("holdout", IN_SAMPLE_END, "2025-12-31")):
                ex1, ex2 = [], []   # excess at 1x and 2x cost
                stops = 0
                for t in trades:
                    if t["bucket"] != b or t["sue"] < thr:
                        continue
                    if not (0.0 < t["reaction"] <= cap):
                        continue
                    if not (lo_d < t["entry_date"] <= hi_d):
                        continue
                    gross, reason, exit_di = t[f"h{H}"]
                    bench = bench_ret(b, t["entry_di"], exit_di)
                    c1 = 2.0 * COST_ONEWAY[b]
                    ex1.append(gross - c1 - bench)
                    ex2.append(gross - 2.0 * c1 - bench)
                    if reason == "stop":
                        stops += 1
                s1 = stats(ex1)
                cell[window] = {"x1": s1, "x2": stats(ex2),
                                "stop_rate": round(stops / len(ex1), 3) if ex1 else None}
            i1, h1, h2 = cell["in_sample"]["x1"], cell["holdout"]["x1"], cell["holdout"]["x2"]
            cell["pass_in_sample"] = bool(i1.get("n", 0) >= 30 and (i1.get("mean") or 0) > 0 and (i1.get("t") or 0) >= 2.0)
            cell["pass_holdout"] = bool(cell["pass_in_sample"] and h1.get("n", 0) >= 30 and (h1.get("mean") or 0) > 0)
            cell["pass_2x"] = bool(cell["pass_holdout"] and (h2.get("mean") or 0) > 0)
            results[key] = cell
            print(f"{key:22s} IS n={i1.get('n',0):5d} m={i1.get('mean',0) or 0:+.4f} t={i1.get('t')} | "
                  f"HO n={h1.get('n',0):5d} m={h1.get('mean',0) or 0:+.4f} t={h1.get('t')} | "
                  f"2x m={h2.get('mean',0) or 0:+.4f} | {'PASS' if cell['pass_2x'] else ('IS-only' if cell['pass_in_sample'] else '-')}",
                  flush=True)

# non-isolated rule: a passing cell needs an adjacent passer (±1 on H or cap)
H_IDX = {h: i for i, h in enumerate(HOLDS)}
C_IDX = {c[0]: i for i, c in enumerate(CAPS)}
def neighbors(b, H, cn):
    out = []
    hi, ci = H_IDX[H], C_IDX[cn]
    for dh in (-1, 1):
        if 0 <= hi + dh < len(HOLDS):
            out.append(f"{b}_h{HOLDS[hi+dh]}_{cn}")
    for dc in (-1, 1):
        if 0 <= ci + dc < len(CAPS):
            out.append(f"{b}_h{H}_{CAPS[ci+dc][0]}")
    return out
supported = []
for b in BUCKETS:
    for H in HOLDS:
        for cn, _ in CAPS:
            key = f"{b}_h{H}_{cn}"
            if results[key]["pass_2x"] and any(results[nb]["pass_2x"] for nb in neighbors(b, H, cn)):
                supported.append(key)

verdict = {"sue_threshold_in_sample_p80": thr, "n_events_priced": len(trades),
           "skipped": skipped, "cells": results, "supported_non_isolated": supported,
           "verdict": "SUPPORTED" if supported else "REFUTED"}
json.dump(verdict, open(f"{OUT}/cells_verdict.json", "w"), indent=1)
print(f"\n=== VERDICT: {verdict['verdict']} | non-isolated survivors: {supported or 'NONE'} ===", flush=True)
