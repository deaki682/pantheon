"""Proteus v2 — the build register (charter v2.1, art. 14).

The build test becomes record: before any build ships, its build-test
sentence is journaled here — the trading decision it improves, the
observable that will show it working, and a kill-spec (the evidence
that would prove the machine is not earning its keep). At every review
(art. 21) each machine is marked EARNING, NOT-YET, or DEAD against its
own sentence; DEAD machinery is pruned that session or its retention
journaled as an override. Machinery is measured by the graded record,
never by count.
"""
from __future__ import annotations

import json
import os

REGISTER_PATH = "cache/proteus_build_register.json"
MARKS = ("NOT-YET", "EARNING", "DEAD")
_FLOOR = 40


class BuildError(ValueError):
    """A machine that can't state its build-test sentence doesn't ship."""


def load_register(path: str = REGISTER_PATH) -> dict:
    if not os.path.exists(path):
        return {"version": 1, "machines": {}}
    reg = json.load(open(path))
    reg.setdefault("machines", {})
    return reg


def save_register(reg: dict, path: str = REGISTER_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(reg, open(path, "w"), indent=1, sort_keys=True)


def register_build(reg: dict, *, name: str, sentence: str, observable: str,
                   kill_spec: str, built: str) -> dict:
    """Art. 14: sentence + observable + kill-spec, before the build ships."""
    if name in reg["machines"]:
        raise BuildError(f"machine {name!r} already registered — mark it, "
                         "don't re-register")
    for label, text in (("sentence", sentence), ("observable", observable),
                        ("kill_spec", kill_spec)):
        if len(text or "") < _FLOOR:
            raise BuildError(f"build {label} must be >= {_FLOOR} chars — "
                             "can't write the sentence, don't build it "
                             "(art. 14)")
    reg["machines"][name] = {
        "sentence": sentence, "observable": observable,
        "kill_spec": kill_spec, "built": built,
        "mark": "NOT-YET", "marks": [],
    }
    return reg


def mark_build(reg: dict, *, name: str, mark: str, date: str,
               note: str = "") -> dict:
    """Review-time mark (art. 21). Append-only history; DEAD is a duty
    to prune that session or journal the retention override."""
    if name not in reg["machines"]:
        raise BuildError(f"unknown machine {name!r}")
    if mark not in MARKS:
        raise BuildError(f"mark must be one of {MARKS}, got {mark!r}")
    m = reg["machines"][name]
    m["mark"] = mark
    m["marks"].append({"date": date, "mark": mark, "note": note})
    return reg
