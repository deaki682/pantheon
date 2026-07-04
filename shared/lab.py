"""The HOUSE research lab — invent, pre-register, backtest, forward-test.

Generalized from proteus/lab.py on 2026-07-04 (operator directive: "our
own, massive, comprehensive research lab"). The engine was god-agnostic
by design; what changed is scope and bookkeeping:

- ONE registry for the whole house (`cache/lab_registry.json`). Any
  sponsor — proteus, the operator, any god's post-mortem — files
  hypotheses into the same pipeline.
- ONE `hypotheses_ever` counter across all sponsors. Sharding the
  multiple-testing denominator per god would let every lab flatter
  itself; the honest count is the house count.
- Every strategy records its `sponsor`, so calibration can later ask
  whose ideas survive contact with data.

The pipeline is a one-way ratchet:

    hypothesis -> preregistered -> backtested -> forward_testing
                                       |               |
                                    refuted        validated | refuted

Mechanical rules (each mirrors a measured house lesson):

- A hypothesis must state the MECHANISM, WHO LOSES on the other side,
  and WHY the edge is underutilized (unarbitraged). "It went up in the
  past" is not a mechanism.
- A backtest cannot be recorded until the strategy is pre-registered
  (prereg doc committed BEFORE data — git timestamps are the proof)
  and every item of BIAS_CHECKLIST is explicitly addressed in writing.
- One dataset buys one decision, once: a second backtest on the same
  strategy is refused without a fresh prereg (house ledger rule).
- Backtest support alone NEVER validates: promotion to `validated`
  requires a forward test — >= MIN_FORWARD_GRADES graded paper trades
  with positive SHRUNK mean excess (oracle.learning.bayesian_shrunk_
  skill; small samples don't get taken at face value here either).
- `refuted` is terminal without a new prereg. Failed studies get the
  same prominence as wins (ledger rule).
- The lab is PAPER ONLY. Nothing here places orders or touches any
  live book; lab forward-test trades do NOT count toward Proteus's
  live checkpoint (prereg amendment #4).
"""
from __future__ import annotations

import json
import os

LAB_PATH = "cache/lab_registry.json"
LAB_GHOST_LEDGER = "cache/lab_ghost_ledger.json"
LAB_GHOST_CURVE = "cache/lab_ghost_curve.json"

MIN_FORWARD_GRADES = 20

STATUSES = ("hypothesis", "preregistered", "backtested", "forward_testing",
            "validated", "refuted", "shelved")

BACKTEST_VERDICTS = ("supported", "refuted", "inconclusive")


class LabError(Exception):
    """Raised when a lab record fails validation. The writer refuses;
    it does not warn."""


# Every backtest record must address ALL of these, in writing, before the
# writer accepts it. The floors are stub-guards, not quality bars — the
# point is that "I didn't think about survivorship" becomes impossible to
# ship silently.
BIAS_CHECKLIST = {
    "survivorship": (
        "How delisted/acquired/bankrupt names are included. A population "
        "built from today's listings is a population of survivors."),
    "look_ahead": (
        "Proof no datum is used before it was publicly knowable (filing "
        "timestamps vs trade dates, restated financials, index membership "
        "as-of dates)."),
    "selection": (
        "How the event population was defined BEFORE results were seen — "
        "complete catalog, not examples that came to mind because they "
        "worked."),
    "multiple_testing": (
        "How many hypotheses/variants were tried against this data, "
        "including abandoned ones — cite the lab's own count. 20 tries "
        "buys one 5%-fluke for free."),
    "overfitting": (
        "Parameter count vs sample size; what was chosen in-sample; what "
        "is held out. A rule with five tuned knobs and forty events is a "
        "description, not a strategy."),
    "costs_liquidity": (
        "Spreads, slippage, and tradability AT SIZE in the actual "
        "names — a thin-name edge can be entirely inside the spread."),
    "regime": (
        "Which market regimes the sample covers and why the edge should "
        "persist outside them (the house has already measured one "
        "warm-vintage +41% collapse to -1% out of regime)."),
    "small_n": (
        "The raw n, the shrunk effect estimate, and what n the forward "
        "test needs before the number means anything."),
}

_HYPOTHESIS_FLOORS = {
    "mechanism": 200,            # why the edge exists, structurally
    "who_loses": 80,             # who is on the other side and why constrained
    "underutilized_because": 80, # why isn't this already arbitraged away
    "falsifiable_claim": 80,     # what measured result would kill it
}

_PREREG_FLOORS = {
    "population_definition": 120,  # the complete catalog, defined blind
    "metric": 40,                  # what is measured, over what horizon
    "success_criteria": 80,        # thresholds committed before data
}

_BIAS_FLOOR = 60  # chars per checklist item


def _shrunk(mean: float, n: int) -> float:
    # Deferred import: shared.* must not import oracle.* at module load
    # (oracle already imports shared modules).
    from oracle.learning import bayesian_shrunk_skill
    return bayesian_shrunk_skill(mean, n)


def load_lab(path: str = LAB_PATH) -> dict:
    if not os.path.exists(path):
        return {"strategies": {}, "hypotheses_ever": 0}
    return json.load(open(path))


def save_lab(lab: dict, path: str = LAB_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(lab, open(path, "w"), indent=1, sort_keys=True)


def _require_prose(record: dict, floors: dict, ctx: str) -> None:
    for name, floor in floors.items():
        if len(str(record.get(name) or "")) < floor:
            raise LabError(
                f"{ctx}: {name} must be at least {floor} chars — "
                f"an unarticulated {name} is not a {name}")


def _get(lab: dict, slug: str) -> dict:
    strat = lab["strategies"].get(slug)
    if strat is None:
        raise LabError(f"unknown strategy {slug!r}")
    return strat


def new_strategy(lab: dict, *, slug: str, date: str, sponsor: str,
                 **fields) -> dict:
    """Register a hypothesis. The idea is free; the articulation is not.

    `sponsor` names who filed it ("proteus", "operator", "oracle", ...) —
    the house counter is shared, but credit and blame are attributed.
    """
    if not slug.isidentifier():
        raise LabError(f"slug must be identifier-like, got {slug!r}")
    if slug in lab["strategies"]:
        raise LabError(f"strategy {slug!r} already exists — no re-cuts")
    sponsor = str(sponsor or "").strip().lower()
    if not sponsor:
        raise LabError("sponsor required — every hypothesis has an author")
    _require_prose(fields, _HYPOTHESIS_FLOORS, f"hypothesis {slug}")
    strat = {
        "slug": slug,
        "sponsor": sponsor,
        "status": "hypothesis",
        "created": date,
        "history": [{"date": date, "to": "hypothesis"}],
        **{k: fields[k] for k in _HYPOTHESIS_FLOORS},
    }
    lab["strategies"][slug] = strat
    lab["hypotheses_ever"] = lab.get("hypotheses_ever", 0) + 1
    return strat


def preregister(lab: dict, slug: str, *, date: str, prereg_doc: str,
                **fields) -> dict:
    """Freeze the test design BEFORE data. `prereg_doc` is the committed
    docs/ path — git history is the timestamp that proves 'before'."""
    strat = _get(lab, slug)
    if strat["status"] != "hypothesis":
        raise LabError(
            f"{slug}: prereg requires status=hypothesis, is {strat['status']!r} "
            "(a refuted or tested strategy needs a NEW slug and fresh prereg)")
    if not str(prereg_doc).startswith("docs/"):
        raise LabError(
            f"{slug}: prereg_doc must be a committed docs/ path, got {prereg_doc!r}")
    _require_prose(fields, _PREREG_FLOORS, f"prereg {slug}")
    strat["prereg"] = {"doc": prereg_doc, "date": date,
                       **{k: fields[k] for k in _PREREG_FLOORS}}
    strat["status"] = "preregistered"
    strat["history"].append({"date": date, "to": "preregistered"})
    return strat


def record_backtest(lab: dict, slug: str, *, date: str, n: int,
                    mean_excess: float, verdict: str,
                    bias_checklist: dict, results_doc: str = "",
                    notes: str = "") -> dict:
    """The only door for a backtest result. Refuses: un-preregistered
    strategies, second backtests, and any unaddressed bias item."""
    strat = _get(lab, slug)
    if strat["status"] != "preregistered":
        raise LabError(
            f"{slug}: backtest requires status=preregistered, is "
            f"{strat['status']!r} — one dataset buys one decision, once")
    if verdict not in BACKTEST_VERDICTS:
        raise LabError(f"verdict {verdict!r} not in {BACKTEST_VERDICTS}")
    if not (isinstance(n, int) and not isinstance(n, bool) and n > 0):
        raise LabError(f"n must be a positive int, got {n!r}")
    missing = [k for k in BIAS_CHECKLIST if k not in (bias_checklist or {})]
    if missing:
        raise LabError(
            f"{slug}: bias checklist incomplete — unaddressed: {missing}. "
            "A backtest that hasn't looked its biases in the eye is a story, "
            "not a result")
    for k in BIAS_CHECKLIST:
        if len(str(bias_checklist[k] or "")) < _BIAS_FLOOR:
            raise LabError(
                f"{slug}: bias item {k!r} must be addressed in >= "
                f"{_BIAS_FLOOR} chars — 'n/a' is not an answer; say WHY it "
                "does not apply")
    strat["backtest"] = {
        "date": date, "n": n,
        "mean_excess": round(float(mean_excess), 6),
        "mean_excess_shrunk": round(_shrunk(float(mean_excess), n), 6),
        "verdict": verdict,
        "bias_checklist": {k: str(bias_checklist[k]) for k in BIAS_CHECKLIST},
        "results_doc": results_doc,
        "notes": notes,
    }
    new_status = "refuted" if verdict == "refuted" else "backtested"
    strat["status"] = new_status
    strat["history"].append({"date": date, "to": new_status})
    return strat


def start_forward_test(lab: dict, slug: str, *, date: str) -> dict:
    """A supported backtest earns a paper forward test — never live money."""
    strat = _get(lab, slug)
    if strat["status"] != "backtested":
        raise LabError(
            f"{slug}: forward test requires status=backtested, is {strat['status']!r}")
    if strat["backtest"]["verdict"] != "supported":
        raise LabError(
            f"{slug}: only a 'supported' backtest earns a forward test "
            f"(got {strat['backtest']['verdict']!r})")
    strat["forward"] = {"started": date, "grades": []}
    strat["status"] = "forward_testing"
    strat["history"].append({"date": date, "to": "forward_testing"})
    return strat


def record_forward_grade(lab: dict, slug: str, *, date: str, symbol: str,
                         excess: float, note: str = "") -> dict:
    """Append one graded paper trade (excess vs the SPY mirror over the
    trade's own window, same convention as the live book)."""
    strat = _get(lab, slug)
    if strat["status"] != "forward_testing":
        raise LabError(
            f"{slug}: cannot grade forward trades in status {strat['status']!r}")
    strat["forward"]["grades"].append({
        "date": date, "symbol": symbol.upper(),
        "excess": round(float(excess), 6), "note": note,
    })
    return strat


def evaluate_forward(lab: dict, slug: str) -> dict:
    """The promotion arithmetic, computed fresh every time it's asked for.
    Judged on the SHRUNK mean — small forward samples don't get face value."""
    strat = _get(lab, slug)
    grades = (strat.get("forward") or {}).get("grades", [])
    xs = [g["excess"] for g in grades]
    n = len(xs)
    mean = sum(xs) / n if n else None
    shrunk = _shrunk(mean, n) if n else None
    return {
        "n": n,
        "needed": MIN_FORWARD_GRADES,
        "mean_excess": round(mean, 6) if mean is not None else None,
        "mean_excess_shrunk": round(shrunk, 6) if shrunk is not None else None,
        "promotable": bool(n >= MIN_FORWARD_GRADES and shrunk and shrunk > 0),
    }


def conclude_forward(lab: dict, slug: str, *, date: str) -> dict:
    """Settle a forward test: validated iff the arithmetic says promotable,
    refuted otherwise. No judgment call, no re-cut."""
    strat = _get(lab, slug)
    if strat["status"] != "forward_testing":
        raise LabError(
            f"{slug}: conclude requires status=forward_testing, is {strat['status']!r}")
    verdict = evaluate_forward(lab, slug)
    if verdict["n"] < MIN_FORWARD_GRADES:
        raise LabError(
            f"{slug}: only {verdict['n']}/{MIN_FORWARD_GRADES} forward grades — "
            "concluding early is the re-cut the rules forbid")
    new_status = "validated" if verdict["promotable"] else "refuted"
    strat["forward"]["verdict"] = verdict
    strat["status"] = new_status
    strat["history"].append({"date": date, "to": new_status})
    return strat


def shelve(lab: dict, slug: str, *, date: str, reason: str) -> dict:
    """Park a hypothesis honestly (data unavailable, cost too high). A
    shelved idea keeps its record; it is not deleted and not refuted."""
    strat = _get(lab, slug)
    if strat["status"] in ("validated", "refuted"):
        raise LabError(f"{slug}: cannot shelve a settled strategy")
    if len(str(reason or "")) < 40:
        raise LabError("a shelving reason under 40 chars is not a reason")
    strat["shelved_reason"] = reason
    strat["status"] = "shelved"
    strat["history"].append({"date": date, "to": "shelved"})
    return strat


def live_citable(lab: dict, sponsor: str | None = None) -> list[str]:
    """Slugs a live thesis may cite as a validated house strategy. Everything
    else can inform a discretionary trade only as an untested idea, argued
    on its own merits in the thesis. Optionally filter by sponsor."""
    return sorted(
        s for s, v in lab["strategies"].items()
        if v["status"] == "validated"
        and (sponsor is None or v.get("sponsor") == sponsor)
    )


def pipeline_summary(lab: dict) -> dict:
    """One-glance state of the house pipeline, by status and sponsor."""
    by_status: dict[str, list[str]] = {}
    by_sponsor: dict[str, int] = {}
    for slug, v in sorted(lab["strategies"].items()):
        by_status.setdefault(v["status"], []).append(slug)
        by_sponsor[v.get("sponsor", "unknown")] = (
            by_sponsor.get(v.get("sponsor", "unknown"), 0) + 1)
    return {
        "hypotheses_ever": lab.get("hypotheses_ever", 0),
        "by_status": by_status,
        "by_sponsor": by_sponsor,
    }
