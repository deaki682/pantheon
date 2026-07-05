"""spinoff_orphans backtest — pre-registered spec (docs/lab_prereg_spinoff_orphans.md).

Benchmark: SEP has no ETFs, so build the size-matched SMALL/MICRO equal-weight
daily index from the achilles panel (data/achilles_gauntlet). Entry T+1 after the
child's first-trade date; excess vs the bucket EW over each window; series ending
mid-hold EXITS AT LAST PRINT and is KEPT (delist). Small/micro tail is the primary
test; full set is the crowded control. In-sample 2015-19 / holdout 2020-24; 2x cost.
"""
import gzip, json, os, bisect, math
from array import array
from collections import defaultdict
import shared.sharadar as sh

OUT = "data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000 + int(s[5:7])*100 + int(s[8:10])
def norm(s):
    s=(s or "").strip()
    if len(s)>=10: return s[:10]
    if len(s)==7: return s+"-15"
    if len(s)==4: return s+"-06-30"
    return "2021-01-01"

# ---- 1. build SMALL+MICRO EW daily index from the achilles panel ----
print("loading achilles panel for the benchmark...", flush=True)
px={}
tmp=defaultdict(lambda:[array('i'),array('f')])
for part in sorted(os.listdir(OUT)):
    if not part.startswith("sep_part"): continue
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        c,ca=r.get("close"),r.get("closeadj")
        if not ca or ca<=0: continue
        t=tmp[r["ticker"]]; t[0].append(d2i(r["date"])); t[1].append(ca)
for tkr,(ds,cas) in tmp.items():
    o=sorted(range(len(ds)),key=lambda i:ds[i])
    px[tkr]=(array('i',(ds[i] for i in o)),array('f',(cas[i] for i in o)))
del tmp
U=json.load(open(f"{OUT}/universes.json"))["universes"]
acc=defaultdict(lambda:[0.0,0])
for snap in sorted(U):
    y,m=int(snap[:4]),int(snap[5:7]); m2,y2=(m+1,y) if m<12 else (1,y+1)
    lo,hi=y2*10000+m2*100+1, y2*10000+m2*100+31
    for b in ("SMALL","MICRO"):
        for tkr in U[snap][b]:
            p=px.get(tkr)
            if not p: continue
            ds,cas=p; j0=bisect.bisect_left(ds,lo); j1=bisect.bisect_right(ds,hi)
            for j in range(max(j0,1),j1):
                cell=acc[ds[j]]; cell[0]+=cas[j]/cas[j-1]-1.0; cell[1]+=1
days=sorted(acc); cum=array('d',[1.0]*(len(days)+1))
for k,dd in enumerate(days):
    s,n=acc[dd]; cum[k+1]=cum[k]*(1.0+(s/n if n else 0.0))
print(f"  benchmark EW index: {len(days)} days {days[0] if days else '?'}..{days[-1] if days else '?'}", flush=True)
def bench(entry_di, exit_di):
    k0=bisect.bisect_right(days,entry_di); k1=bisect.bisect_right(days,exit_di)
    if k1<=k0 or k1>=len(cum): return 0.0
    return cum[k1]/cum[k0]-1.0

# ---- 2. resolve + fetch spinoff child bars ----
use=json.load(open("/tmp/claude-0/-home-user-pantheon/652257dc-837a-5af7-b21d-88fe3ac01ec1/scratchpad/spinoff_use.json"))
print(f"resolving {len(use)} spinoff tickers...", flush=True)
resolved={}
for s in use:
    try: resolved[s["child_ticker"]]=sh.resolve_ticker(s["child_ticker"], as_of=norm(s["first_trade_date"])).get("ticker") or s["child_ticker"]
    except Exception: resolved[s["child_ticker"]]=None
fins=sorted({v for v in resolved.values() if v})
rows=sh.fetch_sep_bulk_range("2015-01-01","2026-01-31", tickers=fins)
sb={}
for r in rows:
    ca=r.get("closeadj")
    if ca and ca>0: sb.setdefault(r["ticker"],{})[r["date"]]=ca
for t in sb: sb[t]=sorted(sb[t].items())
print(f"  got bars for {len(sb)}/{len(fins)} child symbols", flush=True)

# ---- 3. per-spinoff excess ----
HOR=[63,126,252]
trades=[]
for s in use:
    fin=resolved.get(s["child_ticker"]); ser=sb.get(fin) if fin else None
    if not ser: continue
    dates=[d for d,_ in ser]; sd=norm(s["first_trade_date"])
    i=bisect.bisect_left(dates,sd); ie=i+1
    if ie>=len(ser): continue
    entry=ser[ie][1]
    if entry<=0: continue
    row={"tkr":s["child_ticker"],"size":s["child_size"],"year":sd[:4],
         "small":s["child_size"] in ("small","micro")}
    ok=False
    for H in HOR:
        jx=min(ie+H,len(ser)-1)
        gross=ser[jx][1]/entry-1.0
        edi=d2i(ser[ie][0]); xdi=d2i(ser[jx][0])
        row[H]=gross-bench(edi,xdi); ok=True
    if ok: trades.append(row)
print(f"priced {len(trades)} spinoffs\n", flush=True)

def stats(xs, cost=0.0):
    xs=[x-cost for x in xs if x is not None]; n=len(xs)
    if n<2: return (n,None,None)
    m=sum(xs)/n; sd=math.sqrt(sum((x-m)**2 for x in xs)/(n-1))
    return (n, round(m,4), round(m/(sd/math.sqrt(n)),2) if sd>0 else None)
def rep(name, sub, cost=0.0):
    print(f"--- {name} (n={len(sub)}) cost={cost} ---")
    for H in HOR:
        n,m,t=stats([r[H] for r in sub], cost)
        print(f"   {H:3d}d excess: n={n:3d} mean={m} t={t}")

C=0.006  # ~30bps roundtrip-ish + slippage; 2x stress = 0.012
small=[r for r in trades if r["small"]]
rep("FULL SET (crowded control)", trades)
rep("SMALL/MICRO tail (PRIMARY)", small)
rep("SMALL tail IN-SAMPLE 2015-19", [r for r in small if r["year"]<"2020"])
rep("SMALL tail HOLDOUT 2020-24", [r for r in small if r["year"]>="2020"])
rep("SMALL tail HOLDOUT @2x cost", [r for r in small if r["year"]>="2020"], C)
print("\n=== criteria 5: does SMALL tail beat FULL-set control at 252d? ===")
_,ms,_=stats([r[252] for r in small]); _,mf,_=stats([r[252] for r in trades])
print(f"   small 252d mean={ms}  vs  full 252d mean={mf}  -> small_beats_full={ms is not None and mf is not None and ms>mf}")
