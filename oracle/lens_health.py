"""Lens health checks — fail loud when a lens silently returns nothing.

A lens that fails *systemically* (wrong URL for every name, a broken query)
produces the exact same output as a lens that legitimately found nothing: an
empty cache. The screen then exits 0 and persists that emptiness as "success".
This module turns that silent failure into a loud one.

For lenses we expect to be non-empty, zero is almost always a bug rather than a
quiet market, so we flag it. The judgment is lens-aware:

  - universe-scaled lenses (insiders, quality) fan out over the equity universe,
    so a small/capped run can legitimately yield zero — only judge them on full
    runs (universe >= FULL_RUN_THRESHOLD).
  - the others (smart_money: curated managers; activist_13d: a date-window
    search) don't depend on the equity universe, so zero is always suspect.
"""
from __future__ import annotations

from dataclasses import dataclass


LENS_SPECS = {
    "insiders":     {"min_expected": 1, "universe_scaled": True},
    "quality":      {"min_expected": 1, "universe_scaled": True},
    "smart_money":  {"min_expected": 1, "universe_scaled": False},
    # activist_13d uses EDGAR FTS (efts.sec.gov) which blocks datacenter IPs
    # (GitHub Actions, etc.). Warn but don't block persist — it's a 12% signal.
    "activist_13d": {"min_expected": 1, "universe_scaled": False, "warn_only": True},
}

FULL_RUN_THRESHOLD = 1000


@dataclass
class LensHealth:
    lens: str
    count: int
    min_expected: int
    enforced: bool
    ok: bool
    reason: str


def assess_lens(
    lens: str, count: int, universe_size: int, *, full_run_threshold: int = FULL_RUN_THRESHOLD,
) -> LensHealth:
    """Judge one lens's result count. Unknown lenses are never flagged."""
    spec = LENS_SPECS.get(lens)
    if spec is None:
        return LensHealth(lens, count, 0, False, True, "no spec — not checked")
    min_expected = spec["min_expected"]
    enforced = (universe_size >= full_run_threshold) if spec["universe_scaled"] else True
    warn_only = spec.get("warn_only", False)
    if not enforced:
        return LensHealth(
            lens, count, min_expected, False, True,
            f"not enforced (universe {universe_size} < {full_run_threshold})",
        )
    healthy = count >= min_expected
    if not healthy and warn_only:
        return LensHealth(
            lens, count, min_expected, True, True,
            f"WARN — {count} results (expected >= {min_expected}), non-fatal",
        )
    reason = "ok" if healthy else f"SYSTEMIC EMPTY — {count} results, expected >= {min_expected}"
    return LensHealth(lens, count, min_expected, True, healthy, reason)


def assess(
    counts: dict[str, int], universe_size: int, *, full_run_threshold: int = FULL_RUN_THRESHOLD,
) -> list[LensHealth]:
    """Assess every lens present in `counts`."""
    return [
        assess_lens(lens, count, universe_size, full_run_threshold=full_run_threshold)
        for lens, count in counts.items()
    ]


def all_ok(healths: list[LensHealth]) -> bool:
    return all(h.ok for h in healths)
