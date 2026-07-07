"""call_evasion — LEXICON arm (docs/lab_prereg_call_evasion.md).

The backtestable baseline: does high Loughran-McDonald UNCERTAINTY-language density
in a filing predict negative forward drift? (The LLM evasion-read is the forward
A/B, not this.) Whole-filing LM density = LM's own method (robust, no fragile MD&A
extraction). Universe: a sample of SMALL-bucket companies (achilles panel returns +
bucket EW benchmark). Entry T+1 after the filing date; forward 63d excess vs
same-bucket EW; high-vs-low uncertainty tercile. In-sample <=2015 / holdout 2016+.
SCOPED for tractability (EDGAR rate-limited); coverage disclosed. PAPER ONLY.
"""
import gzip, json, os, bisect, math, time
from collections import defaultdict
import shared.edgar as e
OUT="data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000+int(s[5:7])*100+int(s[8:10])

# Loughran-McDonald uncertainty lexicon (core; ~ the LM uncertainty list)
LM=set("""approximate approximately uncertain uncertainty uncertainties risk risks risked risking risky rough roughly may
might could possible possibly probable probably contingent contingency contingencies depend depends depended depending
dependent fluctuate fluctuates fluctuated fluctuating fluctuation fluctuations indefinite indefinitely variable variability
variables unpredictable unclear unknown unknowns unforeseen unforeseeable assume assumed assumes assuming assumption
assumptions estimate estimates estimated estimating believe believes believed anticipate anticipates anticipated
anticipating expose exposure exposures exposed pending precaution precautionary speculate speculative tentative tentatively
volatility volatile sudden suddenly seldom occasionally somewhat nearly apparent apparently conceivable conceivably
imprecise improbable intangible reconsider recalculate turbulence uncertainly""".split())

# ---- 1. month-end panel returns + SMALL bucket EW benchmark ----
# MEMORY SCOPE: only load daily bars for tickers in the SMALL universe (a few
# thousand), not all 11,824 -- loading every daily bar OOM-killed the first run.
U=json.load(open(f"{OUT}/universes.json"))["universes"]
NEEDED=set()
for snap in U:
    NEEDED |= set(U[snap]["SMALL"])
print(f"loading panel (scoped to {len(NEEDED)} SMALL-universe tickers)...", flush=True)
mk=defaultdict(list)  # ticker -> [(dateint, closeadj)] sorted
for part in sorted(f for f in os.listdir(OUT) if f.startswith("sep_part")):
    for r in json.load(gzip.open(f"{OUT}/{part}","rt")):
        if r["ticker"] not in NEEDED: continue
        ca=r.get("closeadj")
        if ca and ca>0: mk[r["ticker"]].append((d2i(r["date"]),ca))
for t in mk: mk[t].sort()
# bucket EW daily index
acc=defaultdict(lambda:[0.0,0])
for snap in sorted(U):
    y,m=int(snap[:4]),int(snap[5:7]); m2,y2=(m+1,y) if m<12 else (1,y+1)
    lo,hi=y2*10000+m2*100+1,y2*10000+m2*100+31
    for tkr in U[snap]["SMALL"]:
        p=mk.get(tkr)
        if not p: continue
        ds=[d for d,_ in p]; j0=bisect.bisect_left(ds,lo); j1=bisect.bisect_right(ds,hi)
        for j in range(max(j0,1),j1):
            cell=acc[p[j][0]]; cell[0]+=p[j][1]/p[j-1][1]-1.0; cell[1]+=1
bdays=sorted(acc); bcum=[1.0]*(len(bdays)+1)
for k,dd in enumerate(bdays):
    s,n=acc[dd]; bcum[k+1]=bcum[k]*(1.0+(s/n if n else 0))
def bench(edi,xdi):
    k0=bisect.bisect_right(bdays,edi); k1=bisect.bisect_right(bdays,xdi)
    return bcum[k1]/bcum[k0]-1.0 if (k1>k0 and k1<len(bcum)) else 0.0
def fwd63(tkr,fdate_i):
    p=mk.get(tkr)
    if not p: return None
    ds=[d for d,_ in p]; i=bisect.bisect_right(ds,fdate_i)  # first bar AFTER filing (T+1)
    if i>=len(p): return None
    jx=min(i+63,len(p)-1)
    r=p[jx][1]/p[i][1]-1.0
    return r-bench(p[i][0],p[jx][0])

# ---- 2. ticker->CIK; pick a scoped SMALL-company sample ----
print("ticker->CIK map...", flush=True)
e.set_rate_limit(6)
t2c={}
for row in e.fetch_company_tickers_rows():
    t2c.setdefault(row["ticker"].upper(),str(row["cik_str"]).zfill(10))
recent_small=set()
for snap in sorted(U)[-60:]:   # last 5yr of snapshots
    recent_small|=set(U[snap]["SMALL"])
sample=sorted(t for t in recent_small if t.upper() in t2c and t in mk)[:220]   # scope: <=220 cos
print(f"  {len(sample)} sampled SMALL companies with CIK + bars", flush=True)

# ---- 3. fetch 10-Q/10-K, whole-filing LM uncertainty density ----
print("fetching filings + scoring uncertainty (scoped)...", flush=True)
events=[]   # (ticker, filing_date_int, unc_density, fwd_excess)
fetched=0
for ci,tkr in enumerate(sample):
    try:
        subs=e.fetch_submissions(t2c[tkr.upper()])
        rec=subs.get("filings",{}).get("recent",{})
    except Exception:
        continue
    forms=rec.get("form",[]); accs=rec.get("accessionNumber",[]); docs=rec.get("primaryDocument",[]); dates=rec.get("filingDate",[])
    got=0
    for j,f in enumerate(forms):
        if f not in ("10-Q","10-K"): continue
        fd=dates[j]
        if not (("2015-01-01")<=fd<=("2024-12-31")): continue
        if got>=8: break            # scope: <=8 filings/company
        fil=e.Filing(cik=t2c[tkr.upper()], accession_no=accs[j], form=f,
                     filing_date=fd, primary_document=docs[j], symbol=tkr)
        try:
            body=e.fetch_body(fil); txt=e.clean_html(body) if body else ""
        except Exception:
            continue
        words=[w.strip('.,;:()$%"\'') for w in txt.lower().split()]
        if len(words)<500: continue
        dens=sum(1 for w in words if w in LM)/len(words)
        ex=fwd63(tkr, d2i(fd))
        if ex is not None:
            events.append((tkr, d2i(fd), dens, ex)); got+=1; fetched+=1
    if ci%25==0: print(f"  {ci}/{len(sample)} cos, {fetched} scored events", flush=True)

print(f"\nscored {len(events)} filing-events", flush=True)
def stats(xs):
    n=len(xs)
    if n<2: return (n,None,None)
    m=sum(xs)/n; sd=math.sqrt(sum((x-m)**2 for x in xs)/(n-1))
    return (n,round(m*100,3),round(m/(sd/math.sqrt(n)),2) if sd>0 else None)

for win,lab in (("in","IN-SAMPLE <=2015"),("out","HOLDOUT 2016+")):
    ev=[e_ for e_ in events if (e_[1]<=20151231)==(win=="in")]
    if len(ev)<30: print(f"{lab}: n={len(ev)} too few"); continue
    ev.sort(key=lambda x:x[2])   # by uncertainty density
    k=len(ev)//3
    lo=[x[3] for x in ev[:k]]; hi=[x[3] for x in ev[-k:]]
    nl,ml,tl=stats(lo); nh,mh,th=stats(hi)
    spread=[a-b for a,b in zip([x[3] for x in ev[-k:]],[x[3] for x in ev[:k]])]
    print(f"\n=== {lab} (n={len(ev)}) 63d excess vs bucket EW ===")
    print(f"  LOW-uncertainty tercile:  mean={ml}% (t {tl}, n={nl})")
    print(f"  HIGH-uncertainty tercile: mean={mh}% (t {th}, n={nh})")
    print(f"  HIGH-minus-LOW spread: {round((mh or 0)-(ml or 0),3)}%  (thesis: high uncertainty UNDERPERFORMS -> negative)")
print("\nVERDICT: lexicon supported iff HIGH-uncertainty names UNDERPERFORM LOW (negative high-minus-low), in-sample AND holdout, t>=2.")
json.dump(events, open(f"{OUT}/call_evasion_events.json","w"))
