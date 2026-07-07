"""Dry-run the cascade cost on the REAL field — no model, no credits.

Loads the packets `run_field_prep.py` wrote and projects reads + tokens down each
god's lens, for the full field AND a small calibration slice, so the weekend
GO/NO-GO is priced before a single credit is spent. Nothing here calls a model.

  python3 run_cascade_estimate.py            # oracle + proteus, full + calib
  python3 run_cascade_estimate.py oracle 200 # oracle, calib slice of 200
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.read_cascade import estimate_cost
from oracle.lens import ORACLE_LENS
from proteus.lens import PROTEUS_LENS

FIELDS = {"oracle": ("cache/oracle_field_packets.json", ORACLE_LENS),
          "proteus": ("cache/proteus_field_packets.json", PROTEUS_LENS)}
# rough recall-first triage keep rate — the cheap tier advances the plausible few
TRIAGE_KEEP = 0.35


def _fmt(tokens: int) -> str:
    return f"{tokens/1e6:.2f}M tok" if tokens >= 1e6 else f"{tokens/1e3:.0f}k tok"


def _report(god: str, n: int, lens, label: str):
    est = estimate_cost(n, lens, keep_rate=TRIAGE_KEEP)
    print(f"\n[{god}] {label}: {n:,} names, triage keep~{int(TRIAGE_KEEP*100)}%", flush=True)
    for t in est["per_tier"]:
        print(f"    {t['tier']:7} ({t['model']:6}) {t['reads']:>6,} reads  {_fmt(t['est_tokens']):>12}",
              flush=True)
    print(f"    {'TOTAL':7} {'':8} {'':>6}         {_fmt(est['est_total_tokens']):>12}", flush=True)
    return est["est_total_tokens"]


def main():
    only = sys.argv[1].lower() if len(sys.argv) > 1 and sys.argv[1].lower() in FIELDS else None
    calib = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 150
    grand = 0
    for god, (path, lens) in FIELDS.items():
        if only and god != only:
            continue
        if not os.path.exists(path):
            print(f"[{god}] {path} missing — run `python3 run_field_prep.py {god}` first", flush=True)
            continue
        data = json.load(open(path))
        n = data["coverage"]["n_packets"]
        _report(god, min(calib, n), lens, f"CALIBRATION slice")
        grand += _report(god, n, lens, "FULL field")
    print(f"\n=== grand total (full runs, both gods where present): {_fmt(grand)} ===", flush=True)
    print("note: est only — actual spend uses per-verdict token counts; the deep tier\n"
          "binds under a real budget, so the full number is the CAP, not the bill.", flush=True)


if __name__ == "__main__":
    main()
