"""The build register (charter v2.1, art. 14) and the order-path manifest
(art. 16) — the manifest's every entry must resolve to real code."""
import importlib
import json
import os

import pytest

from proteus.builds import (BuildError, load_register, mark_build,
                            register_build, save_register)

_S = "s" * 40


def test_register_round_trip(tmp_path):
    path = str(tmp_path / "builds.json")
    reg = load_register(path)
    register_build(reg, name="iv_kink_detector", sentence=_S, observable=_S,
                   kill_spec=_S, built="2026-07-13")
    save_register(reg, path)
    got = load_register(path)
    assert got["machines"]["iv_kink_detector"]["mark"] == "NOT-YET"


def test_build_test_sentence_required():
    reg = load_register("/nonexistent")
    with pytest.raises(BuildError, match="sentence"):
        register_build(reg, name="x", sentence="too short", observable=_S,
                       kill_spec=_S, built="2026-07-13")
    with pytest.raises(BuildError, match="kill_spec"):
        register_build(reg, name="x", sentence=_S, observable=_S,
                       kill_spec="", built="2026-07-13")


def test_no_silent_reregistration():
    reg = load_register("/nonexistent")
    register_build(reg, name="x", sentence=_S, observable=_S, kill_spec=_S,
                   built="2026-07-13")
    with pytest.raises(BuildError, match="already registered"):
        register_build(reg, name="x", sentence=_S, observable=_S,
                       kill_spec=_S, built="2026-07-13")


def test_marks_are_append_only_history():
    reg = load_register("/nonexistent")
    register_build(reg, name="x", sentence=_S, observable=_S, kill_spec=_S,
                   built="2026-07-13")
    mark_build(reg, name="x", mark="EARNING", date="2026-08-13", note="n")
    mark_build(reg, name="x", mark="DEAD", date="2026-09-13", note="n")
    assert reg["machines"]["x"]["mark"] == "DEAD"
    assert [m["mark"] for m in reg["machines"]["x"]["marks"]] == \
        ["EARNING", "DEAD"]
    with pytest.raises(BuildError):
        mark_build(reg, name="x", mark="FINE", date="2026-09-13")


def test_order_path_manifest_resolves():
    """Art. 16: the manifest names the material order/sizing/kill-path
    surface. Every entry must import and resolve — a manifest pointing
    at dead names can't gate anything."""
    path = os.path.join(os.path.dirname(__file__), "..", "proteus",
                        "order_path_manifest.json")
    manifest = json.load(open(path))
    entries = (manifest["order_path"] + manifest["sizing_path"]
               + manifest["kill_path"])
    assert len(entries) >= 20
    for dotted in entries:
        parts = dotted.split(".")
        obj = None
        for i in range(len(parts), 0, -1):
            try:
                obj = importlib.import_module(".".join(parts[:i]))
                remainder = parts[i:]
                break
            except ImportError:
                continue
        assert obj is not None, f"{dotted}: no importable module prefix"
        for attr in remainder:
            assert hasattr(obj, attr), f"{dotted}: {attr} not found"
            obj = getattr(obj, attr)
