"""avoidance_direct ROBUSTNESS — is the avoidance-alpha real avoidance, or just the
gross-profitability (quality) factor in disguise? Decompose the distress composite
into its 4 components, run each ALONE as the exclusion signal, + per-year holdout.
Same engine as run_avoidance_direct.py. PAPER ONLY.
"""
import gzip, json, os, bisect, math
from collections import defaultdict
OUT="data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000+int(s[5:7])*100+int(s[8:10])

print("loading panel (month-end)...", flush=True)
bars=defaultdict(dict)
for part in sorted(f for f in os.listdir(OUT) if f.startswith("sep_part")):
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        ca=r.get("closeadj")
        if not ca or ca<=0: continue
        ym=r["date"][:7]; di=d2i(r["date"]); c=bars[r["ticker"]].get(ym)
        if c is None or di>c[0]: bars[r["ticker"]][ym]=(di,ca)
def fwd(tkr,ym):
    m=bars.get(tkr)
    if not m or ym not in m: return None
    y,mo=int(ym[:4]),int(ym[5:]); nmo,ny=(mo+1,y) if mo<12 else (1,y+1); nym=f"{ny:04d}-{nmo:02d}"
    return m[nym][1]/m[ym][1]-1.0 if nym in m else None

print("loading SF1...", flush=True)
sf1=defaultdict(list)
for part in sorted(f for f in os.listdir(OUT) if f.startswith("sf1_arq_part")):
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        a=r.get("assets")
        if not a or a<=0: continue
        sf1[r["ticker"]].append((r["datekey"],(r.get("netinc") or 0)/a,(r.get("ncfo") or 0)/a,(r.get("gp") or 0)/a,r.get("shareswa") or 0))
for t in sf1: sf1[t].sort()
def inp(tkr,ym):
    rows=sf1.get(tkr)
    if not rows: return None
    i=bisect.bisect_right([r[0] for r in rows], f"{ym[:4]}-{ym[5:]}-01")-1
    if i<0: return None
    _,roa,cfoa,gpoa,sw=rows[i]
    dil=sw/rows[i-4][4]-1.0 if (i>=4 and rows[i-4][4]>0) else None
    return roa,cfoa,gpoa,dil

U=json.load(open(f"{OUT}/universes.json"))["universes"]
def rankz(vals):
    xs=sorted(v for v in vals.values() if v is not None)
    def pr(v):
        return 0.5 if v is None or not xs else bisect.bisect_left(xs,v)/max(1,len(xs))
    return {k:pr(v) for k,v in vals.items()}

K=0.10
# signals: each returns "distress rank" (high=exclude). components + composite.
def build(members,ym):
    di={t:inp(t,ym) for t in members}
    roa=rankz({t:(di[t][0] if di[t] else None) for t in members})
    cfoa=rankz({t:(di[t][1] if di[t] else None) for t in members})
    gpoa=rankz({t:(di[t][2] if di[t] else None) for t in members})
    dil=rankz({t:(di[t][3] if di[t] else None) for t in members})
    return {
     "ROA-only":{t:1-roa[t] for t in members},
     "CFOA-only":{t:1-cfoa[t] for t in members},
     "GPOA-only (quality)":{t:1-gpoa[t] for t in members},
     "Dilution-only":{t:dil[t] for t in members},
     "COMPOSITE":{t:(1-roa[t])+(1-cfoa[t])+(1-gpoa[t])+dil[t] for t in members},
    }
SIGS=["ROA-only","CFOA-only","GPOA-only (quality)","Dilution-only","COMPOSITE"]
acc={s:{"in":[],"out":[]} for s in SIGS}
yr_comp=defaultdict(list)
for snap in sorted(U):
    y,m=int(snap[:4]),int(snap[5:7]); nmo,ny=(m+1,y) if m<12 else (1,y+1); hy=f"{ny:04d}-{nmo:02d}"
    win="in" if snap<="2015-12-31" else "out"
    members=[t for b in("SMALL","MICRO") for t in U[snap][b]]
    rets={t:fwd(t,hy) for t in members}; members=[t for t in members if rets[t] is not None]
    if len(members)<50: continue
    full=sum(rets[t] for t in members)/len(members)
    sigs=build(members,hy); nex=max(1,int(K*len(members)))
    for s in SIGS:
        surv=set(sorted(members,key=lambda t:-sigs[s][t])[nex:])
        a=sum(rets[t] for t in surv)/len(surv)-full
        acc[s][win].append(a)
        if s=="COMPOSITE" and win=="out": yr_comp[hy[:4]].append(a)

def st(xs):
    n=len(xs)
    if n<2: return (n,None,None)
    mn=sum(xs)/n; sd=math.sqrt(sum((x-mn)**2 for x in xs)/(n-1))
    return (n,round(mn*100,3),round(mn/(sd/math.sqrt(n)),2) if sd>0 else None)

print("\n=== avoidance-alpha by SIGNAL (k=10%, monthly %, exclude top-distress) ===")
print("Question: does GPOA-only (quality) explain the composite? If GPOA-only ~= composite, it's the quality factor, not 'avoidance'.")
for s in SIGS:
    n,mi,ti=st(acc[s]["in"]); n2,mo,to=st(acc[s]["out"])
    print(f"  {s:22s} IN mean={mi}% t={ti} | HOLDOUT mean={mo}% t={to}")
print("\n=== COMPOSITE holdout avoidance-alpha BY YEAR (is it one year or persistent?) ===")
for yr in sorted(yr_comp):
    n,mn,t=st(yr_comp[yr]); print(f"  {yr}: mean={mn}%/mo t={t} (n={n})")
