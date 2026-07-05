"""Oracle A/B — does the deep-research dossier beat the screen it came from?

The reframe (docs/oracle_reframe_2026-07-05.md) measures the dossier edge
instead of assuming it. Every candidate the lenses surface is recorded with its
mechanical lens score AND whether the LLM's dossier selected it. Two books:
  - Arm B (mechanical baseline): top-N by lens score from the pool, equal-weight.
  - Arm A (dossier): the LLM's concentrated, conviction-weighted picks.
At each name's horizon both are graded on realized excess vs SPY.
Oracle LLM-lift = Arm A - Arm B: positive => the research adds alpha; zero/
negative => the dossiers are rationalization and Oracle folds into Proteus.
"""
from __future__ import annotations

import json
import os
from shared.gauntlet import convexity_stats

AB_PATH = "cache/oracle_ab.json"


def load_ab(path: str = AB_PATH) -> dict:
    if not os.path.exists(path):
        return {"candidates": [], "graded": []}
    return json.load(open(path))


def save_ab(ab: dict, path: str = AB_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(ab, open(path, "w"), indent=1)


def record_selection(ab: dict, *, round_id: str, date: str, candidates: list,
                     baseline_n: int = 8) -> dict:
    """Record a selection round. `candidates`: list of dicts each with symbol,
    lens_score, llm_selected(bool), conviction, floor_pct, upside_x,
    entry_price, spy_entry, catalyst. The mechanical Arm-B baseline is the
    top-`baseline_n` by lens_score (marked arm_b). Deduped on symbol+round."""
    existing = {(c["symbol"], c["round_id"]) for c in ab["candidates"]}
    ranked = sorted(candidates, key=lambda c: -float(c.get("lens_score", 0)))
    baseline = {c["symbol"] for c in ranked[:baseline_n]}
    for c in candidates:
        key = (c["symbol"].upper(), round_id)
        if key in existing:
            continue
        ab["candidates"].append({
            "round_id": round_id, "date": date, "symbol": c["symbol"].upper(),
            "lens_score": round(float(c.get("lens_score", 0)), 4),
            "arm_a_llm": bool(c.get("llm_selected", False)),
            "arm_b_screen": c["symbol"] in baseline,
            "conviction": c.get("conviction"),
            "floor_pct": c.get("floor_pct"), "upside_x": c.get("upside_x"),
            "catalyst": c.get("catalyst", ""),
            "entry_price": round(float(c.get("entry_price", 0)), 4),
            "spy_entry": round(float(c.get("spy_entry", 0)), 4), "resolved": False,
        })
    return ab


def record_grade(ab: dict, *, round_id: str, symbol: str, exit_price: float,
                 exit_date: str, spy_exit: float) -> dict:
    sym = symbol.upper()
    c = next((x for x in ab["candidates"]
              if x["symbol"] == sym and x["round_id"] == round_id and not x["resolved"]), None)
    if c is None:
        raise ValueError(f"{sym}/{round_id}: no open candidate to grade")
    net = exit_price / c["entry_price"] - 1.0 if c["entry_price"] else 0.0
    spy = spy_exit / c["spy_entry"] - 1.0 if c["spy_entry"] else 0.0
    c["resolved"] = True
    ab["graded"].append({
        **{k: c[k] for k in ("round_id", "symbol", "arm_a_llm", "arm_b_screen",
                             "lens_score", "conviction", "floor_pct", "upside_x")},
        "exit_price": round(float(exit_price), 4), "exit_date": exit_date,
        "net_return": round(net, 6), "spy_return": round(spy, 6),
        "excess": round(net - spy, 6),
    })
    return ab


def llm_lift(ab: dict) -> dict:
    """Arm A (dossier-selected) vs Arm B (top-by-lens-score screen), on realized
    excess-vs-SPY. The headline the reframe is judged on."""
    g = ab["graded"]
    a = [x["excess"] for x in g if x["arm_a_llm"]]
    b = [x["excess"] for x in g if x["arm_b_screen"]]
    # names the LLM PASSED that the screen would have bought — the discriminating set
    passed = [x["excess"] for x in g if x["arm_b_screen"] and not x["arm_a_llm"]]
    A = convexity_stats(a) if a else {"n": 0}
    B = convexity_stats(b) if b else {"n": 0}
    lift = (A.get("expectancy", 0.0) - B.get("expectancy", 0.0)) if (a and b) else None
    return {
        "n_graded": len(g),
        "arm_A_dossier": A,
        "arm_B_screen": B,
        "screen_picks_llm_passed": convexity_stats(passed) if passed else {"n": 0},
        "oracle_llm_lift": round(lift, 4) if lift is not None else None,
        "verdict": ("dossiers add alpha" if (lift or 0) > 0 else
                    "dossiers neutral/negative -> fold into Proteus" if lift is not None
                    else "insufficient graded data"),
    }
