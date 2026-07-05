"""residual_momentum_llm — base-signal backtest (docs/lab_prereg_residual_momentum_llm.md).

Factor-neutral (residual) 12-1 momentum vs RAW 12-1 momentum, on the SMALL bucket
(achilles panel; LARGE pending a bar pull). Residual = regress each name's trailing
36 monthly returns on the bucket-EW ('market') return, take residuals, cumulate over
t-12..t-2 (skip last month). Long top-N=50 EW, monthly rebalance, excess vs bucket EW,
turnover-based 2x cost. In-sample <=2015 / holdout 2016+. Base must clear AND beat the
raw-momentum control (criterion 4). PAPER ONLY.
"""
import gzip, json, os, math
from collections import defaultdict
OUT="data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000+int(s[5:7])*100+int(s[8:10])

print("loading panel -> monthly returns...", flush=True)
mk=defaultdict(dict)   # ticker -> {ym:(dateint,closeadj)} last bar each month
for part in sorted(f for f in os.listdir(OUT) if f.startswith("sep_part")):
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        ca=r.get("closeadj")
        if not ca or ca<=0: continue
        ym=r["date"][:7]; di=d2i(r["date"]); c=mk[r["ticker"]].get(ym)
        if c is None or di>c[0]: mk[r["ticker"]][ym]=(di,ca)
# monthly return series
def all_months():
    s=set()
    for t in mk: s|=set(mk[t])
    return sorted(s)
MONTHS=all_months()
midx={m:i for i,m in enumerate(MONTHS)}
ret=defaultdict(dict)  # ticker -> {ym: monthly return}
for t,mm in mk.items():
    ms=sorted(mm)
    for a,b in zip(ms,ms[1:]):
        if midx[b]==midx[a]+1:
            ret[t][b]=mm[b][1]/mm[a][1]-1.0
print(f"  {len(ret)} tickers, {len(MONTHS)} months", flush=True)

U=json.load(open(f"{OUT}/universes.json"))["universes"]
# bucket-EW ('market') monthly return series from SMALL membership
mkt={}
for snap in sorted(U):
    y,m=int(snap[:4]),int(snap[5:7]); nmo,ny=(m+1,y) if m<12 else (1,y+1)
    hy=f"{ny:04d}-{nmo:02d}"
    rs=[ret[t][hy] for t in U[snap]["SMALL"] if hy in ret.get(t,{})]
    if rs: mkt[hy]=sum(rs)/len(rs)

def signal(tkr, upto_idx):
    """residual & raw 12-1 momentum ending at month index upto_idx (inclusive of t-2)."""
    r=ret.get(tkr,{})
    # need months upto_idx-35 .. upto_idx for 36-mo beta; skip most recent (t-1) -> use t-12..t-2
    win=[MONTHS[i] for i in range(upto_idx-35,upto_idx+1) if 0<=i]
    if len(win)<30: return None,None
    pairs=[(ret[tkr][mn],mkt[mn]) for mn in win if mn in r and mn in mkt]
    if len(pairs)<24: return None,None
    xs=[p[1] for p in pairs]; ys=[p[0] for p in pairs]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    var=sum((x-mx)**2 for x in xs)
    beta=(sum((x-mx)*(y-my) for x,y in pairs)/var) if var>0 else 0.0
    alpha=my-beta*mx
    # residual momentum over t-12..t-2 (skip last month = upto_idx)
    seg=[MONTHS[i] for i in range(upto_idx-11,upto_idx) if 0<=i]   # 11 months t-12..t-2
    resid=0.0; raw=1.0; nseg=0
    for mn in seg:
        if mn in r and mn in mkt:
            resid+=r[mn]-(alpha+beta*mkt[mn]); raw*=(1+r[mn]); nseg+=1
    if nseg<8: return None,None
    return resid, raw-1.0

def stats(xs):
    n=len(xs)
    if n<2: return (n,None,None)
    m=sum(xs)/n; sd=math.sqrt(sum((x-m)**2 for x in xs)/(n-1))
    return (n,round(m*100,3),round(m/(sd/math.sqrt(n)),2) if sd>0 else None)

print("simulating...", flush=True)
N=50; COST=0.003
res={s:{"in":[],"out":[]} for s in("resid","raw")}
prev={"resid":set(),"raw":set()}
turn={"resid":[],"raw":[]}
for snap in sorted(U):
    y,m=int(snap[:4]),int(snap[5:7]); nmo,ny=(m+1,y) if m<12 else (1,y+1)
    hy=f"{ny:04d}-{nmo:02d}"
    if hy not in midx or hy not in mkt: continue
    ti=midx[hy]-1   # signal known as of the snapshot month (t-1 rel to hold)
    win="in" if snap<="2015-12-31" else "out"
    members=[t for t in U[snap]["SMALL"] if hy in ret.get(t,{})]
    if len(members)<80: continue
    bench=sum(ret[t][hy] for t in members)/len(members)
    sig={}
    for t in members:
        rm,rw=signal(t,ti)
        if rm is not None: sig[t]=(rm,rw)
    if len(sig)<N*2: continue
    for key,idx in(("resid",0),("raw",1)):
        top=sorted(sig,key=lambda t:-sig[t][idx])[:N]
        r=sum(ret[t][hy] for t in top)/len(top)-bench
        tn=len(set(top)^prev[key])/(2*N) if prev[key] else 1.0
        res[key][win].append(r-COST*tn)   # net of turnover cost (1x); 2x reported below
        turn[key].append(tn); prev[key]=set(top)

print("\n=== RESIDUAL vs RAW 12-1 momentum — monthly excess vs SMALL-bucket EW (net 1x cost) ===")
for key in("resid","raw"):
    for w in("in","out"):
        n,mm,tt=stats(res[key][w])
        print(f"  {key:6s} {w:3s}: mean={mm}%/mo  t={tt}  (n={n})")
avg_turn=sum(turn['resid'])/len(turn['resid']) if turn['resid'] else 0
print(f"\navg monthly turnover (resid): {avg_turn:.2f}  -> annual cost drag ~{avg_turn*COST*12*100:.1f}% (2x = {avg_turn*COST*24*100:.1f}%)")
# 2x-cost holdout check
res2=[x-COST*t for x,t in zip(res['resid']['out'],turn['resid'][-len(res['resid']['out']):])] if res['resid']['out'] else []
n2,m2,t2=stats(res2)
print(f"resid holdout @~2x cost: mean={m2}%/mo t={t2}")
print("\nVERDICT: supported iff RESID excess>0 t>=2 in-sample+holdout, positive @2x cost, AND resid>raw. Prior: likely refuted at the cost gate.")
