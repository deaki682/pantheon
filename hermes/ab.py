"""Hermes A/B — the LLM-lift measurement (docs/hermes_launch_override.md).

Every detected cash deal is recorded ONCE with the LLM's keep/drop verdict.
Both arms trade the same detected universe:
  - Arm B (paper, mechanical): EVERY detected deal.
  - Arm A (live, LLM): only the deals the LLM kept (and that fit the sizing cap).
At resolution each deal gets its per-arm return. LLM-lift = the convexity/return
of Arm A (kept) minus Arm B (all) — the dollar answer to "does the LLM read a
deal better than a screen?" This is the whole experiment; the numbers decide,
not the story.
"""
from __future__ import annotations

import json
import os
from shared.gauntlet import convexity_stats

AB_PATH = "cache/hermes_ab.json"


def load_ab(path: str = AB_PATH) -> dict:
    if not os.path.exists(path):
        return {"detected": [], "graded": []}
    return json.load(open(path))


def save_ab(ab: dict, path: str = AB_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(ab, open(path, "w"), indent=1)


def record_detection(ab: dict, *, symbol: str, detect_date: str, entry_price: float,
                     offer_price: float, spy_entry: float, expected_close: str,
                     llm_verdict: str, llm_rationale: str, break_risk: str,
                     arm_a_live: bool) -> dict:
    """Record a detected deal + the LLM's read. `llm_verdict` in {keep, drop};
    `arm_a_live` True iff it was actually taken with real money (kept AND fit the
    sizing cap). Deduped on symbol+detect_date."""
    if llm_verdict not in ("keep", "drop"):
        raise ValueError(f"llm_verdict must be keep|drop, got {llm_verdict!r}")
    key = (symbol.upper(), detect_date)
    if any((d["symbol"], d["detect_date"]) == key for d in ab["detected"]):
        return ab
    ab["detected"].append({
        "symbol": symbol.upper(), "detect_date": detect_date,
        "entry_price": round(float(entry_price), 4), "offer_price": round(float(offer_price), 4),
        "spy_entry": round(float(spy_entry), 4), "expected_close": expected_close,
        "spread": round(offer_price / entry_price - 1.0, 4) if entry_price else 0.0,
        "llm_verdict": llm_verdict, "llm_rationale": llm_rationale,
        "break_risk": break_risk, "arm_a_live": bool(arm_a_live), "resolved": False,
    })
    return ab


def record_resolution(ab: dict, *, symbol: str, exit_price: float, exit_date: str,
                      spy_exit: float, outcome: str) -> dict:
    """Resolve the open detection for `symbol`: compute the per-arm return and
    move it to graded. Return = exit/entry - 1 (excess vs SPY too)."""
    sym = symbol.upper()
    det = next((d for d in ab["detected"] if d["symbol"] == sym and not d["resolved"]), None)
    if det is None:
        raise ValueError(f"{sym}: no open detection to resolve")
    net = exit_price / det["entry_price"] - 1.0 if det["entry_price"] else 0.0
    spy = spy_exit / det["spy_entry"] - 1.0 if det["spy_entry"] else 0.0
    det["resolved"] = True
    ab["graded"].append({
        **{k: det[k] for k in ("symbol", "detect_date", "entry_price", "offer_price",
                               "spread", "llm_verdict", "break_risk", "arm_a_live")},
        "exit_price": round(float(exit_price), 4), "exit_date": exit_date,
        "outcome": outcome, "net_return": round(net, 6),
        "spy_return": round(spy, 6), "excess": round(net - spy, 6),
    })
    return ab


def llm_lift(ab: dict) -> dict:
    """The headline: convexity of Arm A (LLM kept) vs Arm B (all detected), and
    the lift. Meaningful once a handful of deals have graded."""
    graded = ab["graded"]
    b_rets = [g["net_return"] for g in graded]                       # all deals (mechanical)
    a_rets = [g["net_return"] for g in graded if g["llm_verdict"] == "keep"]  # LLM kept
    dropped = [g["net_return"] for g in graded if g["llm_verdict"] == "drop"]  # LLM avoided
    A = convexity_stats(a_rets) if a_rets else {"n": 0}
    B = convexity_stats(b_rets) if b_rets else {"n": 0}
    D = convexity_stats(dropped) if dropped else {"n": 0}
    lift = (A.get("expectancy", 0.0) - B.get("expectancy", 0.0)) if (a_rets and b_rets) else None
    return {
        "n_graded": len(graded),
        "arm_A_llm_kept": A,
        "arm_B_mechanical_all": B,
        "arm_dropped_by_llm": D,           # if these did WORSE, the LLM avoided the right ones
        "llm_lift_expectancy": round(lift, 4) if lift is not None else None,
        "verdict": ("LLM adds value" if (lift or 0) > 0 else
                    "LLM neutral/negative" if lift is not None else "insufficient data"),
    }
