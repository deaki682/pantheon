"""Registry discipline (charter v2.1, arts. 2, 3, 10)."""
import pytest

from proteus.registry import (RegistryError, empty_registry, load_registry,
                              reclassify, register_class, register_tag,
                              require_class, require_tags, resolve_class,
                              save_registry)


def _reg():
    reg = empty_registry()
    register_class(reg, name="odd_lot_tender",
                   definition="Buy 99 shares or fewer of a listed odd-lot-priority tender target below the offer; tender all.",
                   ledger_family="tender_arb", hunting_ground="odd_lot_tender",
                   created="2026-07-13", capacity_capped=True)
    register_tag(reg, kind="failure_mode", name="deal_break",
                 definition="The announced deal or tender is withdrawn, amended down, or fails to close.",
                 why_no_existing="first tag of its kind in a fresh registry",
                 created="2026-07-13")
    register_tag(reg, kind="judgment_type", name="document_read",
                 definition="A judgment formed by reading the primary document (filing, transcript, order) for the name.",
                 why_no_existing="first tag of its kind in a fresh registry",
                 created="2026-07-13")
    return reg


def test_round_trip(tmp_path):
    path = str(tmp_path / "reg.json")
    reg = _reg()
    save_registry(reg, path)
    assert load_registry(path) == reg


def test_missing_registry_loads_empty(tmp_path):
    assert load_registry(str(tmp_path / "nope.json")) == empty_registry()


def test_class_requires_definition_family_ground():
    reg = empty_registry()
    with pytest.raises(RegistryError):
        register_class(reg, name="x", definition="too short",
                       ledger_family="f", hunting_ground="g",
                       created="2026-07-13")
    with pytest.raises(RegistryError):
        register_class(reg, name="x", definition="d" * 40,
                       ledger_family="", hunting_ground="g",
                       created="2026-07-13")


def test_class_refuses_redefinition():
    reg = _reg()
    with pytest.raises(RegistryError):
        register_class(reg, name="odd_lot_tender", definition="d" * 40,
                       ledger_family="f", hunting_ground="g",
                       created="2026-07-13")


def test_new_tag_requires_why_no_existing():
    reg = _reg()
    with pytest.raises(RegistryError):
        register_tag(reg, kind="failure_mode", name="regulator_block",
                     definition="d" * 40, why_no_existing="because",
                     created="2026-07-13")


def test_require_class_and_tags():
    reg = _reg()
    require_class(reg, "odd_lot_tender")
    require_tags(reg, "failure_mode", ["deal_break"])
    with pytest.raises(RegistryError):
        require_class(reg, "unregistered")
    with pytest.raises(RegistryError):
        require_tags(reg, "judgment_type", ["vibes"])


def test_reclassify_is_append_only_and_resolves():
    reg = _reg()
    register_class(reg, name="tender_arb_v2", definition="d" * 40,
                   ledger_family="tender_arb", hunting_ground="odd_lot_tender",
                   created="2026-07-13")
    with pytest.raises(RegistryError):
        reclassify(reg, old="odd_lot_tender", new="tender_arb_v2",
                   mapping_note="too short", date="2026-07-13")
    reclassify(reg, old="odd_lot_tender", new="tender_arb_v2",
               mapping_note="n" * 40, date="2026-07-13")
    assert "odd_lot_tender" in reg["strategy_classes"]  # the past stands
    assert resolve_class(reg, "odd_lot_tender") == "tender_arb_v2"
    assert resolve_class(reg, "tender_arb_v2") == "tender_arb_v2"
