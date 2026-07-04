"""Compatibility shim — the lab engine now lives in shared.lab.

Generalized 2026-07-04 (operator directive: house-wide research lab).
The registry moved from `cache/proteus_lab.json` (frozen with a
`superseded_by` marker; still a guard file, still holding the terminal
verdicts recorded before the move) to the HOUSE registry
`cache/lab_registry.json`, with a single house-wide `hypotheses_ever`
counter — sharding the multiple-testing denominator per god would let
every lab flatter itself.

Everything importable here re-exports from shared.lab unchanged, so
`from proteus import lab as L` keeps working. New strategies must name
their `sponsor` ("proteus" for /proteus-lab sessions).
"""
from shared.lab import (  # noqa: F401
    BACKTEST_VERDICTS,
    BIAS_CHECKLIST,
    LAB_GHOST_CURVE,
    LAB_GHOST_LEDGER,
    LAB_PATH,
    LabError,
    MIN_FORWARD_GRADES,
    STATUSES,
    conclude_forward,
    evaluate_forward,
    live_citable,
    load_lab,
    new_strategy,
    pipeline_summary,
    preregister,
    record_backtest,
    record_forward_grade,
    save_lab,
    shelve,
    start_forward_test,
)

# Legacy alias: lab errors were JournalError before the generalization.
JournalError = LabError

# Frozen pre-migration registry (guard file; do not write to it).
LEGACY_LAB_PATH = "cache/proteus_lab.json"
