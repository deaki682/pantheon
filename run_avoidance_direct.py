"""avoidance_direct — MECHANICAL arm (docs/lab_prereg_avoidance_direct.md).

The load-bearing test: does excluding MECHANICALLY-DISTRESSED names beat excluding
RANDOM names? If mechanical avoidance can't beat random, the whole 'LLM=avoidance'
thesis is refuted before the LLM arm is even built. Universe = SMALL/MICRO PIT
(achilles panel; LARGE pending a bar pull). Distress composite from SF1 (limited
cols: netinc/assets, ncfo/assets, gp/assets, shareswa dilution). PIT by datekey.
Monthly rebalance; exclude top-k% distress; 'avoidance alpha' = survivors EW minus
full-universe EW forward 1mo, averaged. Arm B (distress) vs Arm C (random) vs the
null. In-sample <=2015 / holdout 2016+. PAPER ONLY.
"""
import gzip, json, os, bisect, math, random
from collections import defaultdict
random.seed(42)
OUT = "data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000+int(s[5:7])*100+int(s[8:10])

# ---- 1. month-end closeadj per ticker from the panel ----
print("loading panel...", flush=True)
bars=defaultdict(dict)   # ticker -> {yyyymm: (dateint, closeadj)}  keep last bar each month
for part in sorted(os.listdir(OUT)):
    if not part.startswith("sep_part"): continue
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        ca=r.get("closeadj")
        if not ca or ca<=0: continue
        ym=r["date"][:7]; di=d2i(r["date"])
        cur=bars[r["ticker"]].get(ym)
        if cur is None or di>cur[0]: bars[r["ticker"]][ym]=(di,ca)
print(f"  {len(bars)} tickers with monthly marks", flush=True)

def fwd_ret(tkr, ym):
    m=bars.get(tkr)
    if not m or ym not in m: return None
    y,mo=int(ym[:4]),int(ym[5:]); nmo,ny=(mo+1,y) if mo<12 else (1,y+1)
    nym=f"{ny:04d}-{nmo:02d}"
    if nym not in m: return None
    return m[nym][1]/m[ym][1]-1.0

# ---- 2. SF1 distress inputs, PIT by datekey ----
print("loading SF1...", flush=True)
sf1=defaultdict(list)  # ticker -> [(datekey, roa, cfoa, gpoa, shareswa)]
for part in sorted(f for f in os.listdir(OUT) if f.startswith("sf1_arq_part")):
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        a=r.get("assets");
        if not a or a<=0: continue
        sf1[r["ticker"]].append((r["datekey"], (r.get("netinc") or 0)/a,
            (r.get("ncfo") or 0)/a, (r.get("gp") or 0)/a, r.get("shareswa") or 0))
for t in sf1: sf1[t].sort()
def distress_inputs(tkr, di_ym):
    rows=sf1.get(tkr)
    if not rows: return None
    dk=f"{di_ym[:4]}-{di_ym[5:]}-01"
    i=bisect.bisect_right([r[0] for r in rows], dk)-1   # latest datekey <= month start
    if i<0: return None
    _,roa,cfoa,gpoa,sw=rows[i]
    dil=None
    if i>=4 and rows[i-4][4]>0: dil=sw/rows[i-4][4]-1.0
    return roa,cfoa,gpoa,dil

# ---- 3. universe months ----
U=json.load(open(f"{OUT}/universes.json"))["universes"]
def rankz(vals):  # dict name->val -> percentile rank (0..1); None -> 0.5
    xs=sorted((v for v in vals.values() if v is not None))
    if not xs: return {k:0.5 for k in vals}
    def pr(v):
        if v is None: return 0.5
        return bisect.bisect_left(xs,v)/max(1,len(xs))
    return {k:pr(v) for k,v in vals.items()}

KS=[0.05,0.10,0.20]
# collect avoidance alpha per (arm, k, window)
acc={(arm,k,w):[] for arm in("distress","random") for k in KS for w in("in","out")}
months=sorted(U)
for snap in months:
    y,m=int(snap[:4]),int(snap[5:7]); nmo,ny=(m+1,y) if m<12 else (1,y+1)
    hold_ym=f"{ny:04d}-{nmo:02d}"   # trade the month AFTER the snapshot
    win="in" if snap<="2015-12-31" else "out"
    members=[t for b in("SMALL","MICRO") for t in U[snap][b]]
    rets={t:fwd_ret(t,hold_ym) for t in members}
    members=[t for t in members if rets[t] is not None]
    if len(members)<50: continue
    full=sum(rets[t] for t in members)/len(members)
    # distress score: high = distressed (low roa/cfoa/gpoa, high dilution)
    di={t:distress_inputs(t,hold_ym) for t in members}
    roa=rankz({t:(di[t][0] if di[t] else None) for t in members})
    cfoa=rankz({t:(di[t][1] if di[t] else None) for t in members})
    gpoa=rankz({t:(di[t][2] if di[t] else None) for t in members})
    dil=rankz({t:(di[t][3] if di[t] else None) for t in members})
    dscore={t:(1-roa[t])+(1-cfoa[t])+(1-gpoa[t])+dil[t] for t in members}  # higher=worse
    ordered=sorted(members,key=lambda t:-dscore[t])
    for k in KS:
        nex=max(1,int(k*len(members)))
        surv=set(ordered[nex:])  # drop the top-k% most distressed
        b=sum(rets[t] for t in surv)/len(surv)-full
        acc[("distress",k,win)].append(b)
        rex=set(random.sample(members,nex)); rsurv=[t for t in members if t not in rex]
        c=sum(rets[t] for t in rsurv)/len(rsurv)-full
        acc[("random",k,win)].append(c)

def stats(xs):
    n=len(xs)
    if n<2: return (n,None,None)
    m=sum(xs)/n; sd=math.sqrt(sum((x-m)**2 for x in xs)/(n-1))
    return (n,round(m*100,3),round(m/(sd/math.sqrt(n)),2) if sd>0 else None)

print("\n=== AVOIDANCE ALPHA (monthly %, survivors-minus-full-universe) ===")
print("positive = excluding those names IMPROVED the basket. distress should beat random(~0).")
for k in KS:
    for w in("in","out"):
        nd,md,td=stats(acc[("distress",k,w)]); nr,mr,tr=stats(acc[("random",k,w)])
        print(f"  k={int(k*100):2d}% {w:3s}: DISTRESS mean={md}%/mo t={td} (n={nd}) | RANDOM mean={mr}%/mo t={tr}")
print("\nVERDICT: mechanical avoidance works iff DISTRESS avoidance-alpha > 0 (t>=2) AND > RANDOM, in-sample AND holdout.")
