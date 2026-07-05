"""Join the BLIND LLM candor scores to the forward returns (revealed only now) and
the lexicon density. Tests: (1) does high-evasion underperform low-evasion at 63d?
(2) does the LLM read beat the Loughran-McDonald word-count on the SAME filings
(the evasion increment)? PAPER ONLY."""
import json, math
OUT="data/achilles_gauntlet"
scores={
"F001":0.52,"F002":0.52,"F003":0.46,"F004":0.28,"F005":0.46,"F006":0.63,"F007":0.18,"F008":0.44,"F009":0.57,
"F010":0.58,"F011":0.50,"F012":0.62,"F013":0.20,"F014":0.15,"F015":0.32,"F016":0.52,"F017":0.50,"F018":0.22,
"F019":0.44,"F020":0.52,"F021":0.33,"F022":0.55,"F023":0.48,"F024":0.40,"F025":0.51,"F026":0.57,"F027":0.39,
"F028":0.52,"F029":0.22,"F030":0.44,"F031":0.33,"F032":0.52,"F033":0.50,"F034":0.30,"F035":0.28,"F036":0.36,
"F037":0.66,"F038":0.67,"F039":0.29,"F040":0.37,"F041":0.33,"F042":0.39,"F043":0.38,"F044":0.43,"F045":0.46,
"F046":0.38,"F047":0.27,"F048":0.60,"F049":0.30,"F050":0.29,"F051":0.43,"F052":0.62,"F053":0.45,
}
man=json.load(open(f"{OUT}/evasion_manifest.json"))
rows=[]  # (fid, llm, lm_density, fwd)
for fid,s in scores.items():
    m=man[fid]; rows.append((fid,s,m["lm_density"],m["fwd_excess"]))
print(f"joined {len(rows)} filings\n")

def stats(xs):
    n=len(xs)
    if n<2: return (n,None,None)
    mn=sum(xs)/n; sd=math.sqrt(sum((x-mn)**2 for x in xs)/(n-1))
    return (n,round(mn*100,2),round(mn/(sd/math.sqrt(n)),2) if sd>0 else None)
def pearson(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    cov=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    va=math.sqrt(sum((x-ma)**2 for x in a)); vb=math.sqrt(sum((y-mb)**2 for y in b))
    r=cov/(va*vb) if va>0 and vb>0 else 0.0
    t=r*math.sqrt((n-2)/(1-r*r)) if abs(r)<1 else float('inf')
    return round(r,3), round(t,2)
def spearman(a,b):
    def rank(v):
        order=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
        for pos,i in enumerate(order): r[i]=pos
        return r
    return pearson(rank(a),rank(b))

llm=[r[1] for r in rows]; dens=[r[2] for r in rows]; fwd=[r[3] for r in rows]

# winsorize forward returns lightly (one +669% outlier dominates otherwise) for the tercile means
def wins(xs,p=0.05):
    s=sorted(xs); lo=s[int(p*len(s))]; hi=s[int((1-p)*len(s))-1]
    return [min(max(x,lo),hi) for x in xs]
fwd_w=wins(fwd)

print("=== correlations: signal vs forward 63d excess (negative = signal predicts underperformance) ===")
for name,sig in (("LLM candor (evasion)",llm),("Lexicon LM-density",dens)):
    r,t=pearson(sig,fwd_w); rs,ts=spearman(sig,fwd)
    print(f"  {name:24s}  Pearson r={r} (t={t}) | Spearman rho={rs} (t={ts})")

print("\n=== terciles by each signal — mean 63d excess (winsorized), thesis: HIGH underperforms LOW ===")
n=len(rows); k=n//3
for name,sig in (("LLM candor",llm),("Lexicon density",dens)):
    idx=sorted(range(n),key=lambda i:sig[i])
    lo=[fwd_w[i] for i in idx[:k]]; hi=[fwd_w[i] for i in idx[-k:]]
    nl,ml,tl=stats(lo); nh,mh,th=stats(hi)
    print(f"  {name:16s} LOW mean={ml}% (n={nl}) | HIGH mean={mh}% (n={nh}) | HIGH-LOW={round((mh or 0)-(ml or 0),2)}%")

# does the LLM add beyond the lexicon? partial: regress fwd on [density, llm], report llm coef sign/t via
# two-var OLS (normal equations)
def ols2(y,x1,x2):
    n=len(y)
    def m(v): return sum(v)/n
    my,m1,m2=m(y),m(x1),m(x2)
    y_=[v-my for v in y]; a=[v-m1 for v in x1]; b=[v-m2 for v in x2]
    saa=sum(v*v for v in a); sbb=sum(v*v for v in b); sab=sum(a[i]*b[i] for i in range(n))
    say=sum(a[i]*y_[i] for i in range(n)); sby=sum(b[i]*y_[i] for i in range(n))
    det=saa*sbb-sab*sab
    if det==0: return None
    beta1=(sbb*say-sab*sby)/det; beta2=(saa*sby-sab*say)/det
    resid=[y_[i]-beta1*a[i]-beta2*b[i] for i in range(n)]
    s2=sum(r*r for r in resid)/(n-3)
    se2=math.sqrt(s2*saa/det)  # se of beta2 (llm)
    return round(beta2,4), round(beta2/se2,2) if se2>0 else None
res=ols2(fwd_w,dens,llm)
print(f"\n=== OLS: fwd ~ lexicon_density + LLM_candor (does LLM add beyond word-count?) ===")
print(f"  LLM_candor coef={res[0]}  t={res[1]}  (negative+significant = LLM candor predicts beyond lexicon)")
print("\nHONEST READ: n=53, one modality (MD&A prose, not call Q&A), 2023-24 only. Directional pre-screen, not a validation.")
