"""Feed the special_situation net — EDGAR spinoff + IPO sweep (2026-07-06).

Enumerates every spinoff-registration (Form 10-12B/A) and IPO-path filer
(S-1 -> 424B4 effective) over the window from EDGAR daily FORM indexes (100%
recall, no keyword), maps CIK->ticker, and deposits typed events into the shared
event calendar so oracle.upside_ranker's special_situation net has a real feed.

Classification (conservative — a plain 424B4 without an S-1 is a seasoned
follow-on, NOT a new-issue special situation, so it is skipped):
  spinoff : filed 10-12B or 10-12B/A
  ipo     : filed 424B4 AND an S-1 in the window (registered then priced)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import forced_seller_sourcing as fss
from shared import edgar, event_calendar as ec

DATE_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-01-06"
DATE_TO = sys.argv[2] if len(sys.argv) > 2 else "2026-07-06"
FORMS = ["10-12B", "10-12B/A", "424B4", "S-1", "S-1/A"]

print(f"enumerating spinoff/IPO forms {DATE_FROM}..{DATE_TO} (EDGAR daily index)...", flush=True)
filers = fss.enumerate_by_form(DATE_FROM, DATE_TO, FORMS, http_get=edgar.http_get)
print(f"  {len(filers)} distinct filers of {FORMS}", flush=True)

print("mapping CIK->ticker (SEC company_tickers)...", flush=True)
t2c = edgar.fetch_company_tickers()                 # {TICKER: cik10}
c2t = {cik: t for t, cik in t2c.items()}

# SPACs / blank-checks and warrant/unit/right tickers are NOT operating-company
# special situations — the S-1->424B4 path catches every SPAC IPO, so filter them.
_SPAC_MARKERS = ("acquisition corp", "acquisition corporation", "capital corp",
                 "blank check", "equity partners", "acquisition company")


def is_spac_or_unit(ticker: str, name: str) -> bool:
    nm = (name or "").lower()
    if any(m in nm for m in _SPAC_MARKERS):
        return True
    # warrant (W), unit (U), right (R) tickers: 5-char ticker ending in W/U/R
    if len(ticker) >= 5 and ticker[-1] in ("W", "U", "R"):
        return True
    return False


events, n_spin, n_ipo, n_spac = [], 0, 0, 0
for cik, e in filers.items():
    forms = e.get("forms", set())
    ticker = c2t.get(cik)
    if not ticker:
        continue
    if is_spac_or_unit(ticker, e.get("name", "")):
        n_spac += 1
        continue
    if forms & {"10-12B", "10-12B/A"}:
        etype = "spinoff"; n_spin += 1
    elif "424B4" in forms and (forms & {"S-1", "S-1/A"}):
        etype = "ipo"; n_ipo += 1
    else:
        continue                                    # seasoned 424B4 follow-on -> not special
    events.append({
        "symbol": ticker, "type": etype, "date": e.get("last", DATE_TO),
        "source": f"EDGAR daily-index {sorted(forms)} first {e.get('first')} (CIK {cik})",
        "note": f"{etype} — {e.get('name','')}",
    })

print(f"classified: {n_spin} spinoffs, {n_ipo} IPOs, {n_spac} SPACs/units filtered "
      f"(of {len(filers)} filers, {len(events)} operating-co events mapped)", flush=True)

# rebuild: drop any events THIS sweep added earlier (idempotent), then add the clean set
_clean = [e for e in ec.load_calendar()
          if not str(e.get("source", "")).startswith("EDGAR daily-index")]
ec.save_calendar(_clean)
print(f"calendar reset to {len(_clean)} non-sweep events; adding {len(events)} clean...", flush=True)
if events:
    res = ec.add_events(events, today="2026-07-06")
    print(f"event calendar: {res}", flush=True)
    print("\nsample:", flush=True)
    for e in events[:20]:
        print(f"  {e['symbol']:6} {e['type']:8} {e['date']}  {e['note'][:50]}", flush=True)
else:
    print("no ticker-mapped spinoff/IPO events this window", flush=True)
