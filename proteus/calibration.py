"""Proteus v2 — calibration ledger and grade counters (charter v2.1).

Constitutional computations, in code, never from recollection (art. 10):

- **Grade counters** feeding Title I's ladders (art. 2): a position
  grade counts toward ladders and gates only if real-money, non-shadow,
  and its journaled worst case was >= 1% of sleeve equity at entry.
- **The Kelly multiplier** (art. 2): one-quarter Kelly until 20
  real-money position grades have matured; thereafter it may rise only
  with measured calibration and never exceeds one-half. The movement
  rule is defined HERE, once: post-20, the ceiling is 0.5 only when the
  aggregate stated-p vs realized-frequency gap over real-money grades is
  <= 10 percentage points; otherwise it stays 0.25. Tightening this rule
  is always permitted; loosening it requires the operator (art. 29).
- **The calibration table** (art. 10): stated p vs realized frequency by
  judgment type and by strategy class. PARTIALs enter at their realized
  fraction of the journaled payoff (art. 6). Shadow grades are tabulated
  separately (art. 8) — they may shrink confidence, never raise it.
- **The drawdown ladder tier** (art. 5).

Weakening any computation here is an integrity-gate offense (art. 15).
"""
from __future__ import annotations

GRADE_CELLS = ("SKILL", "LUCK", "UNLUCKY", "ERROR")
THESIS_VERDICTS = ("HIT", "MISS", "PARTIAL")
PNL_VERDICTS = ("PAID", "UNPAID")

LADDER_WORST_CASE_FLOOR = 0.01     # art. 2: grades count only if wc >= 1% equity
PROBE_CLASS_GRADES = 3             # art. 2: probe-sized until 3 real grades
HALF_AGG_CLASS_GRADES = 10         # art. 2: class sum <= half agg cap until 10
KELLY_STEP_GRADES = 20             # art. 2: quarter-Kelly until 20 real grades
KELLY_BASE = 0.25
KELLY_MAX = 0.50
KELLY_CAL_GAP = 0.10               # post-20 step-up needs |p - realized| <= this


def kelly_fraction(p: float, payoff_per_unit_worst_case: float) -> float:
    """Kelly f* = p - (1-p)/b, with b in units of the journaled worst case
    (art. 2 binds the cap on worst case, so odds are per unit of worst
    case, never per unit of notional)."""
    b = payoff_per_unit_worst_case
    if not (0.0 < p < 1.0):
        raise ValueError(f"p must be in (0,1), got {p!r}")
    if not b or b <= 0:
        raise ValueError(f"payoff per unit worst case must be > 0, got {b!r}")
    return p - (1.0 - p) / b


def grades(records: list) -> list[dict]:
    return [r for r in records if r.get("action") == "grade"]


def real_money_position_grades(records: list, strategy_class: str | None = None,
                               registry: dict | None = None) -> int:
    """Ladder counter (art. 2). Shadow and flat-month grades never count;
    neither does a grade whose entry worst case was under 1% of equity.
    With a registry, class names follow the reclassification chain."""
    n = 0
    for g in grades(records):
        if g.get("shadow") or g.get("flat_month"):
            continue
        if not g.get("real_money"):
            continue
        if float(g.get("worst_case_pct_at_entry") or 0) < LADDER_WORST_CASE_FLOOR:
            continue
        if strategy_class is not None:
            cls = g.get("strategy_class")
            if registry is not None:
                from proteus.registry import resolve_class
                cls = resolve_class(registry, cls)
            if cls != strategy_class:
                continue
        n += 1
    return n


def allowed_kelly_multiplier(records: list) -> float:
    """The prevailing Kelly multiplier ceiling (art. 2). Defined once;
    see module docstring for the movement rule."""
    total = real_money_position_grades(records)
    if total < KELLY_STEP_GRADES:
        return KELLY_BASE
    table = calibration_table(records)
    agg = table.get("aggregate", {}).get("real_money")
    if agg and agg["n"] > 0 and abs(agg["mean_p"] - agg["realized"]) <= KELLY_CAL_GAP:
        return KELLY_MAX
    return KELLY_BASE


def _realized_value(g: dict) -> float:
    """A grade's realized frequency contribution. HIT=1, MISS=0,
    PARTIAL=its realized fraction of the journaled payoff (art. 6)."""
    v = g.get("thesis_verdict")
    if v == "HIT":
        return 1.0
    if v == "MISS":
        return 0.0
    if v == "PARTIAL":
        frac = g.get("realized_fraction")
        if frac is None or not (0.0 <= float(frac) <= 1.0):
            raise ValueError(
                "a PARTIAL grade must carry realized_fraction in [0,1] "
                f"(art. 6), got {frac!r}")
        return float(frac)
    raise ValueError(f"thesis_verdict must be one of {THESIS_VERDICTS}, got {v!r}")


def calibration_table(records: list) -> dict:
    """Stated p vs realized frequency, by judgment type and by strategy
    class, real-money and shadow tabulated separately (arts. 8, 10)."""
    buckets: dict = {}

    def _add(section: str, key: str, g: dict) -> None:
        arm = "shadow" if g.get("shadow") else "real_money"
        b = buckets.setdefault(section, {}).setdefault(key, {}).setdefault(
            arm, {"n": 0, "sum_p": 0.0, "sum_realized": 0.0})
        b["n"] += 1
        b["sum_p"] += float(g["stated_p"])
        b["sum_realized"] += _realized_value(g)

    for g in grades(records):
        if g.get("stated_p") is None:
            continue
        _add("aggregate", "all", g)
        if g.get("judgment_type"):
            _add("by_judgment_type", g["judgment_type"], g)
        if g.get("strategy_class"):
            _add("by_class", g["strategy_class"], g)

    out: dict = {}
    for section, keys in buckets.items():
        for key, arms in keys.items():
            for arm, b in arms.items():
                row = {"n": b["n"],
                       "mean_p": round(b["sum_p"] / b["n"], 4),
                       "realized": round(b["sum_realized"] / b["n"], 4)}
                if section == "aggregate":
                    out.setdefault("aggregate", {})[arm] = row
                else:
                    out.setdefault(section, {}).setdefault(key, {})[arm] = row
    return out


def drawdown_tier(equity: float, peak_equity: float) -> int:
    """Art. 5: 0 = full caps; 1 = below -25% from peak (caps halve);
    2 = below -40% (new risk confined to the single best-graded class)."""
    if peak_equity <= 0:
        return 0
    dd = 1.0 - equity / peak_equity
    if dd > 0.40:
        return 2
    if dd > 0.25:
        return 1
    return 0
