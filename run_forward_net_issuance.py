"""Forward test for gauntlet_v2's net-issuance-low N50 LARGE (the validated
version). Self-contained: pulls fresh Sharadar data. PAPER ONLY.

  python3 run_forward_net_issuance.py roll     # grade matured quarter + open next
  python3 run_forward_net_issuance.py status   # show open + graded

Convention (frozen, matches the validated backtest): signal at quarter-end
(SF1 datekey<=D), universe = top-500 by DAILY marketcap, long the 50 lowest
trailing-4Q weighted-shares change, equal weight, ENTRY at the next trading
day's close, hold to next quarter-end, grade basket total-return excess vs SPY.
Records one graded quarter per rebalance to the lab (>=20 to conclude).
"""
from __future__ import annotations
import json, os, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh

TRACKER = "cache/lab_forward_net_issuance.json"

def quarter_ends_through(today):
    out=[]
    for y in range(2026, int(today[:4])+1):
        for m,d in ((3,31),(6,30),(9,30),(12,31)):
            qe=f"{y}-{m:02d}-{d:02d}"
            if "2026-06-30" <= qe <= today: out.append(qe)
    return out

def top500(D):
    for off in range(6):
        dd=(date(*map(int,D.split('-')))-timedelta(days=off)).isoformat()
        rows=sh._datatable("DAILY",**{"date.gte":dd,"date.lte":dd,
            "qopts.columns":"ticker,marketcap","qopts.per_page":10000})
        if rows: break
    m={r["ticker"].upper():r["marketcap"] for r in rows if r.get("marketcap")}
    return set(sorted(m,key=lambda t:-m[t])[:500])

def net_issuance_basket(D, universe):
    syms=sorted(universe)
    rows=[]
    for i in range(0,len(syms),90):
        rows+=sh._datatable("SF1",ticker=",".join(syms[i:i+90]),dimension="ARQ",**{
            "calendardate.gte":"2023-01-01","qopts.columns":"ticker,datekey,calendardate,shareswa",
            "qopts.per_page":10000})
    from collections import defaultdict
    byt=defaultdict(list)
    for r in rows:
        if r.get("shareswa") is not None: byt[r["ticker"]].append(r)
    for t in byt: byt[t].sort(key=lambda r:(r["calendardate"],r["datekey"]))
    cand=[]
    for t in universe:
        u=[r for r in byt.get(t,[]) if r["datekey"]<=D]
        if len(u)<8: continue
        l8=u[-8:]
        if l8[-1]["calendardate"] < (date(*map(int,D.split('-')))-timedelta(days=400)).isoformat(): continue
        sc=sum(r["shareswa"] for r in l8[4:]); sp=sum(r["shareswa"] for r in l8[:4])
        if sp>0: cand.append((sc/sp-1.0,t))
    cand.sort()
    return [t for _,t in cand[:50]]

def closeadj(syms, D, table="SEP"):
    out={}
    for i in range(0,len(syms),40):
        for r in sh._datatable(table,ticker=",".join(syms[i:i+40]),**{
            "date.gte":D,"date.lte":D,"qopts.columns":"ticker,closeadj","qopts.per_page":10000}):
            if r.get("closeadj") is not None: out[r["ticker"].upper()]=float(r["closeadj"])
    return out

def next_trading_close(syms, after_D):
    for off in range(1,8):
        dd=(date(*map(int,after_D.split('-')))+timedelta(days=off)).isoformat()
        px=closeadj(syms[:5], dd)
        if px:
            full=closeadj(syms, dd); spy=closeadj(["SPY"], dd, "SFP").get("SPY")
            return dd, full, spy
    return None, {}, None

def main():
    phase = sys.argv[1] if len(sys.argv)>1 else "status"
    t = json.load(open(TRACKER))
    today = date.today().isoformat() if False else None  # Date.now blocked in some envs
    # use latest SEP date as "today"
    probe=sh._datatable("SEP",ticker="AAPL",**{"date.gte":"2026-01-01","qopts.columns":"ticker,date","qopts.per_page":10000})
    today=max(r["date"][:10] for r in probe)
    print(f"data-current through {today}")
    if phase=="status":
        print(json.dumps({"open":[{k:o[k] for k in ('quarter','entry_date','grade_due','n')} for o in t["open"]],
                          "graded":t["graded_quarters"]}, indent=1)); return
    # roll: grade matured open positions, open new quarters
    from shared.lab import load_lab, save_lab, record_forward_grade
    from pantheon.persist import persist
    lab=load_lab(); graded_any=False
    still_open=[]
    for o in t["open"]:
        # matured if the next quarter-end has passed and we have prices there
        gd=o["grade_due"]
        exitpx=closeadj(list(o["positions"]), gd); spy_exit=closeadj(["SPY"],gd,"SFP").get("SPY")
        if len(exitpx)>=0.8*o["n"] and spy_exit:
            rets=[exitpx[s]/o["positions"][s]-1 for s in o["positions"] if s in exitpx]
            basket_ret=sum(rets)/len(rets)
            spy_ret=spy_exit/o["spy_entry"]-1
            excess=basket_ret-spy_ret
            record_forward_grade(lab,"gauntlet_v2_fundamentals",date=gd,
                symbol=o["quarter"],excess=excess,
                note=f"net-issuance basket {basket_ret:+.2%} vs SPY {spy_ret:+.2%}, n={len(rets)}")
            t["graded_quarters"].append({"quarter":o["quarter"],"basket_ret":round(basket_ret,4),
                "spy_ret":round(spy_ret,4),"excess":round(excess,4),"graded":gd})
            graded_any=True
            print(f"GRADED {o['quarter']}: basket {basket_ret:+.2%} vs SPY {spy_ret:+.2%} = excess {excess:+.2%}")
        else:
            still_open.append(o)
    t["open"]=still_open
    # open any quarter-end that's passed and isn't tracked
    tracked={o["quarter"] for o in t["open"]}|{g["quarter"] for g in t["graded_quarters"]}
    for qe in quarter_ends_through(today):
        q=f"{qe[:4]}Q{(int(qe[5:7])-1)//3+1}"
        if q in tracked: continue
        uni=top500(qe); basket=net_issuance_basket(qe, uni)
        ed, px, spy = next_trading_close(basket, qe)
        if not ed or spy is None:
            print(f"{q}: entry data not yet available, skip"); continue
        gd_month=(int(qe[5:7])%12)+3; gd_year=int(qe[:4])+(1 if int(qe[5:7])>9 else 0)
        gm=((int(qe[5:7])-1)//3*3+3)%12+3
        # next quarter-end
        qi=(int(qe[5:7])-1)//3
        nq=[(3,31),(6,30),(9,30),(12,31)][(qi+1)%4]; ny=int(qe[:4])+(1 if qi==3 else 0)
        grade_due=f"{ny}-{nq[0]:02d}-{nq[1]:02d}"
        t["open"].append({"quarter":q,"signal_date":qe,"entry_date":ed,"grade_due":grade_due,
            "spy_entry":spy,"positions":{s:px[s] for s in basket if s in px},
            "n":len([s for s in basket if s in px])})
        print(f"OPENED {q}: {len([s for s in basket if s in px])} names, entry {ed}, grade due {grade_due}")
    open(TRACKER,"w").write(json.dumps(t,indent=1))
    if graded_any: save_lab(lab); persist("lab",{"cache/lab_registry.json":json.dumps(lab,indent=1)})
    persist("lab",{TRACKER:json.dumps(t,indent=1)})
    # --- also grade the buyback-quality A/B arms (diagnostic, same exit prices) ---
    ABF="cache/lab_buyback_quality_ab.json"
    if os.path.exists(ABF):
        ab=json.load(open(ABF)); still=[]
        for o in ab["open"]:
            exitpx=closeadj(list(o["entry_px"]), o["grade_due"]); spy_x=closeadj(["SPY"],o["grade_due"],"SFP").get("SPY")
            if exitpx and spy_x and len(exitpx)>=0.7*len(o["entry_px"]):
                spy_ret=spy_x/o["spy_entry"]-1; row={"quarter":o["quarter"],"spy_ret":round(spy_ret,4),"arms":{}}
                for arm,names in o["arms"].items():
                    rr=[exitpx[s]/o["entry_px"][s]-1 for s in names if s in exitpx and s in o["entry_px"]]
                    if rr:
                        br=sum(rr)/len(rr); row["arms"][arm]={"ret":round(br,4),"excess":round(br-spy_ret,4),"n":len(rr)}
                ab["graded"].append(row)
                L=row["arms"].get("L",{}).get("excess"); R=row["arms"].get("R",{}).get("excess")
                print(f"A/B {o['quarter']}: R {row['arms'].get('R',{}).get('excess')} M {row['arms'].get('M',{}).get('excess')} L {L} | L-R {round((L-R),4) if (L is not None and R is not None) else None}")
            else:
                still.append(o)
        ab["open"]=still; open(ABF,"w").write(json.dumps(ab,indent=1))
        persist("lab",{ABF:json.dumps(ab,indent=1)})

    n_graded=len(t["graded_quarters"])
    print(f"tracker updated: {len(t['open'])} open, {n_graded}/20 graded quarters")

if __name__=="__main__": main()
