"""Live forced-seller sweep — Oracle's coverage spine in action (2026-07-06).

Sweeps every LIVE forced-seller family across the whole EDGAR filing universe
over a recent window, excludes names already tracked, and writes the NEW
candidates to cache/oracle_sourced_candidates.json for the dossier->verify
pipeline. This is the "find the best of thousands" half: names surfaced by a
STRUCTURAL forced-seller event, not by tripping one of the four narrow lenses.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import forced_seller_sourcing as fss

DATE_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-05-01"
DATE_TO = sys.argv[2] if len(sys.argv) > 2 else "2026-07-06"

# Exclude names we already track, so the sweep surfaces only what's NEW:
exclude = set()
for path, extract in [
    ("cache/oracle_convex_dossiers.json", lambda d: []),  # dossiers keyed by ticker, not cik
    ("cache/nemesis_pipeline.json", lambda d: list(d.keys())),
]:
    if os.path.exists(path):
        try:
            exclude |= set(extract(json.load(open(path))))
        except Exception:
            pass
print(f"excluding {len(exclude)} already-tracked CIKs", flush=True)
print(f"sweeping {DATE_FROM}..{DATE_TO} across {len(fss.LIVE_FAMILIES)} live families:", flush=True)
for f in fss.LIVE_FAMILIES:
    print(f"   - {f.key:20s} {f.forms}  q={f.query!r}", flush=True)

cands = fss.sweep(DATE_FROM, DATE_TO, exclude_ciks=exclude)

print(f"\n=== {len(cands)} NEW forced-seller candidates ===", flush=True)
for c in cands:
    tags = "+".join(c.get("families", []))
    tick = c.get("ticker") or "?"
    print(f"  {tick:8s} {c['company'][:42]:42s} [{tags}]  filed {c.get('first_filed','?')}  (cik {c['cik']})", flush=True)

out = {"swept": f"{DATE_FROM}..{DATE_TO}", "n": len(cands), "candidates": cands}
json.dump(out, open("cache/oracle_sourced_candidates.json", "w"), indent=2)
print(f"\nwrote cache/oracle_sourced_candidates.json ({len(cands)} candidates -> dossier->verify pipeline)", flush=True)
