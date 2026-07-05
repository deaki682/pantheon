"""call_evasion — LLM EVASION-READ arm, blind-packet builder.

The lexicon arm (run_call_evasion.py) counted Loughran-McDonald uncertainty words:
inconclusive (high-minus-low -1.96%/63d, t=-0.75, no in-sample). This builds the
LLM arm: re-fetch a STRATIFIED sample of the same filing-events, extract the MD&A
narrative, and write BLIND packets (text only, an opaque id) so a reader scores
management candor/evasion with NO sight of the forward return or the lexicon score.
A private manifest keeps id -> (ticker, date, fwd_excess, lm_density) for the join
AFTER scoring. HONEST SCOPE: EDGAR gives prepared MD&A prose, NOT call Q&A, so this
is a management-CANDOR read (an increment over word-counting), not the full
Q&A-non-answer evasion arm (that stays transcript-blocked). PAPER ONLY.
"""
import gzip, json, os, bisect, math, time
from collections import defaultdict
import shared.edgar as e
from evasion_extract import mdna_prose
OUT="data/achilles_gauntlet"
def d2i(s): return int(s[:4])*10000+int(s[5:7])*100+int(s[8:10])

ev=json.load(open(f"{OUT}/call_evasion_events.json"))   # (ticker, fdate_i, lm_density, fwd_excess)
print(f"{len(ev)} scored events", flush=True)

# ---- stratify by LM density into terciles; sample spread across tickers ----
ev.sort(key=lambda x:x[2])
n=len(ev); k=n//3
terciles={"low":ev[:k],"mid":ev[k:2*k],"high":ev[2*k:]}
PER=18                       # per tercile -> ~36 filings
seen_tkr=defaultdict(int)
sample=[]
for band,rows in terciles.items():
    # walk from the extreme end of each band inward, cap 2 per ticker, spread years
    ordered = rows[::-1] if band=="high" else rows      # high: densest first; low: sparsest first
    picked=0
    for r in ordered:
        if picked>=PER: break
        tkr=r[0]
        if seen_tkr[tkr]>=2: continue
        seen_tkr[tkr]+=1; picked+=1
        sample.append((band,)+tuple(r))
print(f"sampled {len(sample)} events across {len(set(s[1] for s in sample))} tickers", flush=True)

# ---- ticker -> CIK ----
e.set_rate_limit(6)
t2c={}
for row in e.fetch_company_tickers_rows():
    t2c.setdefault(row["ticker"].upper(),str(row["cik_str"]).zfill(10))

# ---- re-fetch each sampled filing, extract MD&A, write blind packet ----
PKT=f"{OUT}/evasion_packets"; os.makedirs(PKT,exist_ok=True)
manifest={}   # id -> {ticker,date,band,lm_density,fwd_excess}
pid=0; written=0
for band,tkr,fdi,dens,fwd in sample:
    fd=f"{str(fdi)[:4]}-{str(fdi)[4:6]}-{str(fdi)[6:]}"
    cik=t2c.get(tkr.upper())
    if not cik: print(f"  skip {tkr}: no CIK",flush=True); continue
    try:
        subs=e.fetch_submissions(cik); rec=subs.get("filings",{}).get("recent",{})
    except Exception as ex:
        print(f"  skip {tkr}: subs {ex}",flush=True); continue
    forms=rec.get("form",[]); accs=rec.get("accessionNumber",[]); docs=rec.get("primaryDocument",[]); dates=rec.get("filingDate",[])
    idx=next((j for j,ff in enumerate(forms) if ff in("10-Q","10-K") and dates[j]==fd),None)
    if idx is None: print(f"  skip {tkr} {fd}: filing not found",flush=True); continue
    fil=e.Filing(cik=cik,accession_no=accs[idx],form=forms[idx],filing_date=fd,primary_document=docs[idx],symbol=tkr)
    try:
        body=e.fetch_body(fil); txt=e.clean_html(body) if body else ""
    except Exception as ex:
        print(f"  skip {tkr} {fd}: body {ex}",flush=True); continue
    excerpt=mdna_prose(txt, target_words=1500, min_words=400)   # robust narrative extract; ""=no real MD&A
    if not excerpt: print(f"  skip {tkr} {fd}: no MD&A prose (BDC/REIT/table-only)",flush=True); continue
    pid+=1; fid=f"F{pid:03d}"
    open(f"{PKT}/{fid}.txt","w").write(
        f"FILING ID: {fid}\nFORM: {forms[idx]}\n"
        "(All company-identifying headers below are as-filed; score ONLY the "
        "management narrative's candor, not the company.)\n\n"+excerpt)
    manifest[fid]={"ticker":tkr,"date":fd,"band":band,"form":forms[idx],
                   "lm_density":dens,"fwd_excess":fwd}
    written+=1
    if written%6==0: print(f"  {written} packets written",flush=True)

json.dump(manifest,open(f"{OUT}/evasion_manifest.json","w"),indent=0)
print(f"\nDONE: {written} blind packets in {PKT}/, manifest -> evasion_manifest.json",flush=True)
