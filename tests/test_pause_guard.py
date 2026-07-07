"""The soft-hold guard: a paused god does not run, but is NOT liquidated (distinct
from the kill switch). Must fail OPEN on a torn file so a god can't wedge off."""
import json

from shared.guards import is_paused, paused_guard


def _write(tmp_path, god, rec):
    (tmp_path / f"{god}_paused.json").write_text(json.dumps(rec))


def test_absent_file_is_not_paused(tmp_path):
    assert is_paused("oracle", cache_dir=str(tmp_path)) is False
    assert paused_guard("oracle", cache_dir=str(tmp_path)) is None


def test_paused_hold_until_manually_lifted(tmp_path):
    _write(tmp_path, "oracle", {"paused": True, "until": None, "reason": "x"})
    # no `until` → paused regardless of date, until the file is changed
    assert is_paused("oracle", today="2026-07-07", cache_dir=str(tmp_path)) is True
    assert is_paused("oracle", today="2027-01-01", cache_dir=str(tmp_path)) is True


def test_dated_pause_expires(tmp_path):
    _write(tmp_path, "oracle", {"paused": True, "until": "2026-07-11"})
    assert is_paused("oracle", today="2026-07-08", cache_dir=str(tmp_path)) is True
    assert is_paused("oracle", today="2026-07-11", cache_dir=str(tmp_path)) is True   # inclusive
    assert is_paused("oracle", today="2026-07-12", cache_dir=str(tmp_path)) is False


def test_paused_false_flag(tmp_path):
    _write(tmp_path, "oracle", {"paused": False, "until": None})
    assert is_paused("oracle", cache_dir=str(tmp_path)) is False


def test_corrupt_file_fails_open(tmp_path):
    (tmp_path / "oracle_paused.json").write_text("{not json")
    assert is_paused("oracle", cache_dir=str(tmp_path)) is False   # never wedge off silently
