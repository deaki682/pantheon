"""Oracle capital allocation.

Starting capital: $1k base, scales toward $12k ceiling only when proven skill:
  - at least 30 graded calls
  - positive alpha with t-statistic >= 2.0
  - high conviction monotonically outperforms low conviction

Reserve $1k of the ceiling for Achilles. Bayesian shrinkage when sample is small.
"""
from __future__ import annotations

from .learning import bayesian_shrunk_skill
from .sleeve import ACHILLES_RESERVE, CAPITAL_BASE, CAPITAL_CEILING


MIN_GRADED_CALLS = 30
MIN_ALPHA_T = 2.0


def compute_allocation(
    *,
    graded_calls: int,
    alpha: float,
    alpha_t: float,
    monotonic_conviction: bool,
    bayesian_prior_n: int = 20,
) -> float:
    """Return the dollar capital allocation for Oracle.

    Returns CAPITAL_BASE unless ALL of the following are true:
      - graded_calls >= MIN_GRADED_CALLS
      - alpha_t >= MIN_ALPHA_T (positive AND significant)
      - alpha > 0
      - monotonic_conviction == True
    """
    if (
        graded_calls < MIN_GRADED_CALLS
        or alpha <= 0
        or alpha_t < MIN_ALPHA_T
        or not monotonic_conviction
    ):
        return CAPITAL_BASE

    # Bayesian shrink: pull observed alpha toward 0 when sample is small.
    shrunk_alpha = bayesian_shrunk_skill(alpha, graded_calls, prior_n=bayesian_prior_n)
    if shrunk_alpha <= 0:
        return CAPITAL_BASE

    # Scale linearly with shrunk alpha; cap at (CEILING - ACHILLES_RESERVE).
    available = CAPITAL_CEILING - ACHILLES_RESERVE
    # Heuristic: alpha 0..0.20 maps to 0..(available - base).
    fraction = min(1.0, shrunk_alpha / 0.20)
    return min(available, CAPITAL_BASE + fraction * (available - CAPITAL_BASE))
