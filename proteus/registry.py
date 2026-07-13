"""Proteus v2 — the controlled registry (charter v2.1, arts. 2, 3, 10).

One machine-readable store for the three controlled taxonomies the
charter binds to the sizing law and the calibration ledger:

- **strategy classes** (art. 2): written definition, ledger family
  (art. 13a) and hunting ground (art. 24) recorded once each — one
  taxonomy, three views. A position's class is fixed at entry; a
  reclassification is an append-only mapping entry, never an edit, and
  may never increase permitted size in the session it lands (the sizing
  ladder reads real-money grades per class, so a rename that would
  reset or merge counts must carry the old→new mapping for the counter
  to follow).
- **failure-mode tags** (art. 3): a new tag requires a written line
  stating why no existing tag applies.
- **judgment-type tags** (art. 10): every prediction carries one at
  write time; calibration is computed per tag.

The registry is state (``cache/proteus_registry.json``), persisted to
the state branch like every other Proteus file. Validation lives here;
the entry schema (proteus.schema) refuses entries whose class or tags
are not registered.
"""
from __future__ import annotations

import json
import os

REGISTRY_PATH = "cache/proteus_registry.json"

_TAG_KINDS = ("failure_mode", "judgment_type")
_WHY_FLOOR = 40      # chars — why no existing tag applies
_DEF_FLOOR = 40      # chars — a definition that can't fill a line isn't one


class RegistryError(ValueError):
    """A taxonomy change that can't justify itself is refused."""


def empty_registry() -> dict:
    return {
        "version": 1,
        "strategy_classes": {},
        "failure_mode": {},
        "judgment_type": {},
        "reclassifications": [],
    }


def load_registry(path: str = REGISTRY_PATH) -> dict:
    if not os.path.exists(path):
        return empty_registry()
    reg = json.load(open(path))
    for key in ("strategy_classes", "failure_mode", "judgment_type"):
        reg.setdefault(key, {})
    reg.setdefault("reclassifications", [])
    return reg


def save_registry(reg: dict, path: str = REGISTRY_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(reg, open(path, "w"), indent=1, sort_keys=True)


def register_class(reg: dict, *, name: str, definition: str,
                   ledger_family: str, hunting_ground: str, created: str,
                   capacity_capped: bool = False) -> dict:
    """Add a strategy class. Refuses redefinition — reclassify instead."""
    if name in reg["strategy_classes"]:
        raise RegistryError(f"class {name!r} already registered — "
                            "use reclassify() with a mapping, never redefine")
    if len(definition or "") < _DEF_FLOOR:
        raise RegistryError(f"class definition must be >= {_DEF_FLOOR} chars")
    if not ledger_family or not hunting_ground:
        raise RegistryError("ledger_family and hunting_ground are recorded "
                            "once each at registration (arts. 13a, 24)")
    reg["strategy_classes"][name] = {
        "definition": definition,
        "ledger_family": ledger_family,
        "hunting_ground": hunting_ground,
        "capacity_capped": bool(capacity_capped),
        "created": created,
    }
    return reg


def register_tag(reg: dict, *, kind: str, name: str, definition: str,
                 why_no_existing: str, created: str) -> dict:
    """Add a failure-mode or judgment-type tag (arts. 3, 10)."""
    if kind not in _TAG_KINDS:
        raise RegistryError(f"tag kind must be one of {_TAG_KINDS}, got {kind!r}")
    if name in reg[kind]:
        raise RegistryError(f"{kind} tag {name!r} already registered")
    if len(definition or "") < _DEF_FLOOR:
        raise RegistryError(f"tag definition must be >= {_DEF_FLOOR} chars")
    if len(why_no_existing or "") < _WHY_FLOOR:
        raise RegistryError(
            f"a new {kind} tag requires >= {_WHY_FLOOR} chars stating why "
            "no existing tag applies (art. 3)")
    reg[kind][name] = {
        "definition": definition,
        "why_no_existing": why_no_existing,
        "created": created,
    }
    return reg


def reclassify(reg: dict, *, old: str, new: str, mapping_note: str,
               date: str) -> dict:
    """Append-only class rename/merge record (art. 2). The old class
    entry is retained (the past stands); the mapping is what lets the
    grade counters follow the name."""
    if old not in reg["strategy_classes"]:
        raise RegistryError(f"unknown class {old!r}")
    if new not in reg["strategy_classes"]:
        raise RegistryError(f"target class {new!r} must be registered first")
    if len(mapping_note or "") < _WHY_FLOOR:
        raise RegistryError(
            f"reclassification requires >= {_WHY_FLOOR} chars of mapping note")
    reg["reclassifications"].append(
        {"old": old, "new": new, "note": mapping_note, "date": date})
    return reg


def resolve_class(reg: dict, name: str) -> str:
    """Follow the reclassification chain to the current class name."""
    seen = set()
    while True:
        nxt = next((r["new"] for r in reg["reclassifications"]
                    if r["old"] == name), None)
        if nxt is None or nxt in seen:
            return name
        seen.add(name)
        name = nxt


def require_class(reg: dict, name: str) -> None:
    if name not in reg["strategy_classes"]:
        raise RegistryError(
            f"strategy class {name!r} is not registered — register it with "
            "its definition, ledger family, and hunting ground first (art. 2)")


def require_tags(reg: dict, kind: str, names) -> None:
    if kind not in _TAG_KINDS:
        raise RegistryError(f"tag kind must be one of {_TAG_KINDS}, got {kind!r}")
    unknown = [n for n in (names or []) if n not in reg[kind]]
    if unknown:
        raise RegistryError(
            f"unregistered {kind} tag(s) {unknown} — a new tag needs its "
            "why-no-existing-tag line (art. 3)")
