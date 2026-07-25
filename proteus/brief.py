"""Proteus v2 — the record brief (charter v2.1, art. 21).

One gate, two edges, computed in code — never from recollection. The
review runs IN THE JOURNAL and produces one artifact, the RECORD BRIEF:

- grades as written (art. 7's four cells, kept vs failed, the LUCK
  count), real-money and shadow/flat-month tabulated separately;
- calibration by judgment type and strategy class (art. 10, delegated
  to proteus.calibration — the constitutional computation);
- the benchmark stack (art. 23, delegated to proteus.benchmark): SPY
  headline plus the deployment-adjusted line;
- the FUNDING EDGE (art. 21a): the preregistered three-part bar that
  converts a proven record into a standing capital claim;
- the NO-EDGE EDGE (art. 21b): failed > kept AND trailing SPY since
  launch => the default posture becomes the park;
- the shortcut summary (art. 11) and the build-register marks (art. 14);
- the invariant-compliance attestation — refused unless all five
  invariants are attested with a written basis.

Counting (art. 2 / art. 21): counted grades are live primaries plus
shadow (art. 8) and flat-month (art. 13b) grades; shadow and flat-month
TOGETHER must stay strictly fewer than half of counted n; the funding
edge's excess-return bar is computed on real-money P&L only (the curve
never contains paper P&L, so the benchmark stack IS the real-money
line). An unauditable grade counts as a FAILED prediction at the review
(art. 28a).

Weakening any test or threshold here is an integrity-gate offense
(art. 15). Tightening is always permitted (art. 29).
"""
from __future__ import annotations

from datetime import date as _date

from proteus import benchmark as bm
from proteus import calibration as cal

INVARIANTS = ("bounded_loss", "kill_switch_first", "integrity_gate",
              "honest_grading", "effort_law")

REVIEW_EVERY_N_GRADES = 20     # art. 21: every 20th graded decision
REVIEW_MAX_DAYS = 90           # ... and in any case at least every 90 days
REVIEW_DRAWDOWN = 0.25         # ... and the first time equity marks -25% from peak
FUNDING_MIN_GRADES = 20        # art. 21a(a)
FUNDING_CAL_GAP = 0.15         # art. 21a(c): stated p within 15pp of realized
_ATTEST_FLOOR = 20             # chars — an attestation needs a written basis


class BriefError(ValueError):
    """A brief that can't attest its own floor is refused."""


def counted_grades(records: list) -> list[dict]:
    """Art. 21's counted set: live primaries + shadow + flat-month."""
    return cal.grades(records)


def _kept(g: dict) -> bool:
    """Thesis axis: HIT and PARTIAL route kept (art. 6); MISS failed.
    An unauditable grade counts FAILED regardless of verdict (art. 28a)."""
    if g.get("unauditable"):
        return False
    return g.get("thesis_verdict") in ("HIT", "PARTIAL")


def grades_as_written(records: list) -> dict:
    """The four cells (art. 7), kept vs failed, LUCK count — real-money
    and shadow/flat-month tabulated separately, as written, no mercy."""
    gs = counted_grades(records)
    out = {
        "n": len(gs),
        "real_money": {"n": 0, "cells": {c: 0 for c in cal.GRADE_CELLS}},
        "shadow": {"n": 0, "cells": {c: 0 for c in cal.GRADE_CELLS}},
        "flat_month": {"n": 0},
        "kept": 0, "failed": 0, "luck": 0, "unauditable": 0,
    }
    for g in gs:
        if _kept(g):
            out["kept"] += 1
        else:
            out["failed"] += 1
        if g.get("unauditable"):
            out["unauditable"] += 1
        if g.get("flat_month"):
            out["flat_month"]["n"] += 1
            continue
        arm = "shadow" if g.get("shadow") else "real_money"
        out[arm]["n"] += 1
        cell = g.get("cell")
        if cell in cal.GRADE_CELLS:
            out[arm]["cells"][cell] += 1
            if cell == "LUCK" and arm == "real_money":
                out["luck"] += 1
    paper = out["shadow"]["n"] + out["flat_month"]["n"]
    out["real_money_majority"] = (out["n"] > 0
                                  and paper < out["n"] - paper)
    return out


def funding_edge(records: list, marks: list,
                 tbill_annual: float = bm.TBILL_ANNUAL_DEFAULT) -> dict:
    """Art. 21a — the preregistered bar. All three legs shown with their
    numbers so the claim (or its absence) is re-derivable."""
    gw = grades_as_written(records)
    dep = bm.deployment_adjusted(marks, tbill_annual)

    # (c) SKILL strictly outnumbering LUCK among P&L-positive matured
    # positions — real money, PARTIALs excluded from the SKILL count.
    skill_strict = luck = 0
    backing_classes: set = set()
    for g in counted_grades(records):
        if g.get("shadow") or g.get("flat_month") or not g.get("real_money"):
            continue
        if g.get("pnl_verdict") != "PAID":
            continue
        if g.get("cell") == "SKILL" and g.get("thesis_verdict") == "HIT":
            skill_strict += 1
            if g.get("strategy_class"):
                backing_classes.add(g["strategy_class"])
        elif g.get("cell") == "LUCK":
            luck += 1

    table = cal.calibration_table(records)
    cal_ok, cal_rows = True, {}
    for cls in sorted(backing_classes):
        row = table.get("by_class", {}).get(cls, {}).get("real_money")
        gap = abs(row["mean_p"] - row["realized"]) if row else None
        cal_rows[cls] = {"row": row, "gap": gap}
        if row is None or gap > FUNDING_CAL_GAP:
            cal_ok = False
    if not backing_classes:
        cal_ok = False   # nothing backs the claim

    legs = {
        "a_sample": {"n": gw["n"], "real_money_majority": gw["real_money_majority"],
                     "pass": gw["n"] >= FUNDING_MIN_GRADES and gw["real_money_majority"]},
        "b_excess": {"deployment_adjusted": dep,
                     "pass": (dep.get("excess_dollars") or 0) > 0},
        "c_skill": {"skill_strict": skill_strict, "luck": luck,
                    "calibration": cal_rows, "cal_within_15pp": cal_ok,
                    "pass": skill_strict > luck and cal_ok},
    }
    legs["pass"] = all(v["pass"] for v in legs.values() if isinstance(v, dict))
    return legs


def no_edge_edge(records: list, marks: list) -> dict:
    """Art. 21b — failed > kept AND trailing SPY since launch => the
    default posture becomes the park."""
    gw = grades_as_written(records)
    head = bm.headline(marks)
    trailing = head.get("excess") is not None and head["excess"] < 0
    return {"kept": gw["kept"], "failed": gw["failed"],
            "headline": head, "trailing_spy": trailing,
            "park_default": gw["failed"] > gw["kept"] and trailing}


def shortcut_summary(records: list) -> dict:
    """Art. 11 — every Effort Law shortcut carries a type tag; recurring
    identical WHY wording is a violation on its face."""
    cuts = [r for r in records if r.get("shortcut_type")]
    by_type: dict = {}
    seen_why: dict = {}
    duplicates = []
    for r in cuts:
        by_type[r["shortcut_type"]] = by_type.get(r["shortcut_type"], 0) + 1
        why = (r.get("why") or r.get("text") or "").strip()
        if why and why in seen_why:
            duplicates.append({"why": why[:120],
                               "dates": [seen_why[why], r.get("date")]})
        seen_why.setdefault(why, r.get("date"))
    return {"n": len(cuts), "by_type": by_type,
            "recurring_identical_why": duplicates,
            "violations": [r for r in cuts if r.get("upgraded_to_violation")]}


def build_register_marks(register: dict) -> dict:
    """Art. 14 — each machine against its own sentence; a machine never
    marked at a review is flagged, not skipped."""
    machines = {}
    for name, m in (register.get("machines") or {}).items():
        machines[name] = {"mark": m.get("mark"),
                          "built": m.get("built"),
                          "n_marks": len(m.get("marks") or []),
                          "never_marked": not (m.get("marks") or [])}
    return {"n": len(machines), "machines": machines,
            "dead_unpruned": [n for n, m in machines.items()
                              if m["mark"] == "DEAD"]}


def brief_due(records: list, marks: list, *, today: str,
              last_brief_date: str | None = None,
              last_brief_grade_count: int = 0,
              drawdown_briefed: bool = False) -> dict:
    """Art. 21's three triggers. Any true => a review is owed THIS
    session; the caller supplies the last brief's date and grade count
    (from the journal — the brief is itself a journal entry)."""
    n = len(counted_grades(records))
    grade_trigger = n - last_brief_grade_count >= REVIEW_EVERY_N_GRADES

    anchor = last_brief_date
    if anchor is None:
        dated = [m["date"] for m in marks if m.get("date")]
        anchor = min(dated) if dated else today
    days = (_date.fromisoformat(str(today)[:10])
            - _date.fromisoformat(str(anchor)[:10])).days
    time_trigger = days >= REVIEW_MAX_DAYS

    ms = [m for m in marks if m.get("equity")]
    dd_trigger = False
    if ms and not drawdown_briefed:
        peak = 0.0
        for m in ms:
            peak = max(peak, float(m["equity"]))
            if peak > 0 and 1.0 - float(m["equity"]) / peak > REVIEW_DRAWDOWN:
                dd_trigger = True
                break
    return {"due": grade_trigger or time_trigger or dd_trigger,
            "grade_trigger": grade_trigger, "grades_since_last": n - last_brief_grade_count,
            "time_trigger": time_trigger, "days_since_last": days,
            "drawdown_trigger": dd_trigger}


def record_brief(records: list, marks: list, register: dict, *,
                 generated: str, attestation: dict,
                 tbill_annual: float = bm.TBILL_ANNUAL_DEFAULT,
                 tbill_source: str = "standing journaled assumption") -> dict:
    """Assemble the one artifact (art. 21). Refuses an attestation that
    does not affirm all five invariants with a written basis — the brief
    exists so the kill switch is always held by an informed hand."""
    errors = []
    for inv in INVARIANTS:
        a = (attestation or {}).get(inv)
        if not isinstance(a, dict) or a.get("compliant") is not True:
            errors.append(f"attestation.{inv} must affirm compliant=True — "
                          "a violation is reported in the brief body, never "
                          "silently attested away")
        elif len(str(a.get("basis") or "")) < _ATTEST_FLOOR:
            errors.append(f"attestation.{inv}.basis must be >= "
                          f"{_ATTEST_FLOOR} chars (art. 28a: re-derivable)")
    extra = set(attestation or {}) - set(INVARIANTS)
    if extra:
        errors.append(f"unknown attestation keys {sorted(extra)}")
    if errors:
        raise BriefError("brief refused:\n- " + "\n- ".join(errors))

    gw = grades_as_written(records)
    return {
        "artifact": "RECORD BRIEF (charter v2.1, art. 21)",
        "generated": generated,
        "grades_as_written": gw,
        "calibration": cal.calibration_table(records),
        "kelly_multiplier": cal.allowed_kelly_multiplier(records),
        "benchmark": {"headline": bm.headline(marks),
                      "deployment_adjusted": bm.deployment_adjusted(
                          marks, tbill_annual),
                      "tbill_annual": tbill_annual,
                      "tbill_source": tbill_source},
        "funding_edge": funding_edge(records, marks, tbill_annual),
        "no_edge_edge": no_edge_edge(records, marks),
        "shortcuts": shortcut_summary(records),
        "build_register": build_register_marks(register),
        "attestation": attestation,
        "counting_note": (
            "counted n = live primaries + shadow (art. 8) + flat-month "
            "(art. 13b); real-money majority "
            + ("HOLDS" if gw["real_money_majority"] else "FAILS — shadow and "
               "flat-month grades must stay strictly fewer than half")),
    }
