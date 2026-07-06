"""Stage-1 answer key + recall measurement (2026-07-06).

Turns "is the sourcing sweep good?" into a NUMBER. For one closed window it
builds the DEFINITIONALLY-COMPLETE set of a forced-seller family by enumerating
EVERY filing of the form that IS the event (from EDGAR's daily form indexes — no
search engine, no keyword), then measures what fraction the current KEYWORD
sweep actually caught (recall). Low recall here is the quantified case for
switching Stage 1 from keyword full-text search to form enumeration.
"""
import json, os, re, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared import edgar

# Families defined by the form that IS the event (complete by construction):
TARGET_FORMS = {
    "SC TO-I":   "issuer tender offer (odd-lot / CEF-discount / Dutch auction live here)",
    "SC TO-I/A": "issuer tender offer (amendment)",
    "N-8F":      "investment-company deregistration (fund wind-down)",
}
WINDOW_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
WINDOW_TO   = sys.argv[2] if len(sys.argv) > 2 else "2026-06-30"

# index line: FORM  NAME  CIK  DATE  FILENAME  (2+ spaces separate fields)
_PAT = re.compile(r"^(.+?)\s{2,}(.+?)\s{2,}(\d+)\s{2,}(\d{4}-\d{2}-\d{2})\s{2,}(\S+)\s*$")


def enumerate_forms(date_from, date_to, forms):
    """Every filer of `forms` in the window, from EDGAR daily form indexes.
    Returns ({cik10: {name, forms:set, first, last, n}}, n_index_days)."""
    formset = set(forms)
    out, days = {}, 0
    d, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
    while d <= end:
        if d.weekday() < 5:  # weekdays only
            url = (f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}"
                   f"/QTR{(d.month - 1)//3 + 1}/form.{d.strftime('%Y%m%d')}.idx")
            try:
                body = edgar.http_get(url)
                text = body if isinstance(body, str) else body.decode("latin-1", errors="replace")
                for line in text.splitlines():
                    m = _PAT.match(line)
                    if not m:
                        continue
                    form = m.group(1).strip()
                    if form not in formset:
                        continue
                    cik = edgar.cik10(m.group(3))
                    e = out.setdefault(cik, {"name": m.group(2).strip(), "forms": set(),
                                             "first": d.isoformat(), "n": 0})
                    e["forms"].add(form); e["n"] += 1; e["last"] = d.isoformat()
                days += 1
            except Exception as ex:
                print(f"  {d}: {type(ex).__name__} (skipped)", flush=True)
        d += timedelta(days=1)
    return out, days


print(f"enumerating {sorted(TARGET_FORMS)} over {WINDOW_FROM}..{WINDOW_TO} from EDGAR daily form indexes...", flush=True)
truth, ndays = enumerate_forms(WINDOW_FROM, WINDOW_TO, TARGET_FORMS)
print(f"  read {ndays} index days -> {len(truth)} distinct filers (the complete answer key)\n", flush=True)

# by-form breakdown
from collections import Counter
byform = Counter()
for e in truth.values():
    for f in e["forms"]:
        byform[f] += 1
for f in sorted(TARGET_FORMS):
    print(f"  {f:10s} {byform.get(f,0):3d} filers  — {TARGET_FORMS[f]}", flush=True)

# --- recall of the keyword sweep ---
swept = {}
if os.path.exists("cache/oracle_sourced_candidates.json"):
    swept = json.load(open("cache/oracle_sourced_candidates.json"))
sweep_ciks = {c["cik"] for c in swept.get("candidates", [])}
truth_ciks = set(truth.keys())
caught = truth_ciks & sweep_ciks
missed = truth_ciks - sweep_ciks
recall = len(caught) / len(truth_ciks) if truth_ciks else 0.0

print(f"\n=== RECALL of the keyword sweep vs the form-enumerated answer key ===", flush=True)
print(f"  answer key (form-enumerated, complete): {len(truth_ciks)}", flush=True)
print(f"  caught by the keyword sweep:            {len(caught)}", flush=True)
print(f"  MISSED by the keyword sweep:            {len(missed)}", flush=True)
print(f"  RECALL = {recall:.0%}", flush=True)
print(f"\n  a sample of what form-enumeration CATCHES that the keyword sweep MISSED:", flush=True)
for cik in list(missed)[:15]:
    e = truth[cik]
    print(f"    {e['name'][:48]:48s} {sorted(e['forms'])}  (cik {cik})", flush=True)

# persist the answer key for the record
for e in truth.values():
    e["forms"] = sorted(e["forms"])
json.dump({"window": f"{WINDOW_FROM}..{WINDOW_TO}", "forms": TARGET_FORMS,
           "index_days": ndays, "n": len(truth),
           "recall_of_keyword_sweep": round(recall, 3),
           "caught": sorted(caught), "missed": sorted(missed),
           "answer_key": truth},
          open("cache/oracle_stage1_answerkey.json", "w"), indent=2)
print(f"\nwrote cache/oracle_stage1_answerkey.json", flush=True)
