"""Live forced-seller sweep — Oracle's coverage spine (2026-07-06, form-enumeration).

PRIMARY sourcing is now FORM ENUMERATION (measured 100% recall vs the keyword
sweep's 12% — see docs/oracle_sourcing_status_2026-07-06.md): enumerate every
filing of the forms that ARE forced-seller events from EDGAR daily indexes, tag
by family, drop the non-traded private-fund noise with a cheap tradability
filter. The keyword sweep is retained only as a supplement for families with no
single defining form (post-BK 8-Ks, rights offerings in S-1/424B prose).
Writes the new tradable candidates to cache/oracle_sourced_candidates.json.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import forced_seller_sourcing as fss

# Window widened 2026-07-06: default to ~3 months (was 2). Override via argv.
DATE_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-04-06"
DATE_TO = sys.argv[2] if len(sys.argv) > 2 else "2026-07-06"

exclude = set()
if os.path.exists("cache/nemesis_pipeline.json"):
    try:
        exclude |= set(json.load(open("cache/nemesis_pipeline.json")).keys())
    except Exception:
        pass

print(f"building the listed-universe ticker map (SEC)...", flush=True)
c2t = fss.cik_to_ticker_map()
print(f"  {len(c2t)} listed CIKs (the tradability filter)", flush=True)
print(f"form-enumerating forced-seller events {DATE_FROM}..{DATE_TO} "
      f"(forms {sorted(fss.FORM_TO_FAMILY)})...", flush=True)

# De-blunted tradability (2026-07-06): enumerate EVERYTHING, then SPLIT into
# tradable (primary) vs non-tradable (flagged) — nothing silently dropped. The
# non-tradable bucket is mostly private funds, but keeps OTC/foreign/newly-listed
# names the SEC ticker file misses available for Stage-2 ticker resolution.
allc = fss.sweep_by_form(DATE_FROM, DATE_TO, cik_to_ticker=c2t,
                         exclude_ciks=exclude, tradable_only=False)
tradable = [c for c in allc if c["tradable"]]
nontradable = [c for c in allc if not c["tradable"]]

print(f"\n=== {len(tradable)} TRADABLE forced-seller candidates (form-enumerated) ===", flush=True)
for c in tradable:
    tags = "+".join(c["families"])
    print(f"  {c['ticker'] or '?':8s} {c['company'][:40]:40s} [{tags}]  {c['forms']}  filed {c['first_filed']}", flush=True)
print(f"\n  (+ {len(nontradable)} non-tradable enumerated events flagged for review, not dropped)", flush=True)

out = {"swept": f"{DATE_FROM}..{DATE_TO}", "method": "form_enumeration; tradable split",
       "n_tradable": len(tradable), "n_nontradable": len(nontradable),
       "candidates": tradable, "nontradable_flagged": nontradable}
json.dump(out, open("cache/oracle_sourced_candidates.json", "w"), indent=2)
print(f"\nwrote cache/oracle_sourced_candidates.json "
      f"({len(tradable)} tradable -> dossier->verify pipeline; {len(nontradable)} flagged)", flush=True)
