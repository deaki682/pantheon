"""Lens health-check tests — the guard that turns silent empties into loud ones."""
from oracle.lens_health import all_ok, assess, assess_lens


def test_universe_scaled_lens_empty_on_full_run_is_flagged():
    h = assess_lens("insiders", 0, universe_size=10_000)
    assert h.enforced is True
    assert h.ok is False
    assert "SYSTEMIC EMPTY" in h.reason


def test_universe_scaled_lens_empty_on_small_run_is_ok():
    # cap=5 test run: zero insider clusters is legitimate, not a bug.
    h = assess_lens("insiders", 0, universe_size=5)
    assert h.enforced is False
    assert h.ok is True


def test_universe_scaled_lens_nonempty_on_full_run_is_ok():
    h = assess_lens("quality", 3998, universe_size=10_000)
    assert h.ok is True


def test_non_universe_lens_empty_always_flagged():
    # smart_money doesn't depend on the equity universe — zero is
    # suspect even on a tiny capped run.
    assert assess_lens("smart_money", 0, universe_size=5).ok is False


def test_warn_only_lens_empty_is_ok_but_warned():
    # activist_13d uses EDGAR FTS which blocks datacenter IPs — warn but don't block.
    h = assess_lens("activist_13d", 0, universe_size=5)
    assert h.ok is True
    assert "WARN" in h.reason


def test_non_universe_lens_nonempty_ok():
    assert assess_lens("smart_money", 12, universe_size=5).ok is True


def test_unknown_lens_never_flagged():
    h = assess_lens("mystery", 0, universe_size=10_000)
    assert h.ok is True
    assert "not checked" in h.reason


def test_assess_and_all_ok_reflects_the_failing_lens():
    # Broken run: insiders + smart_money dead, activist warned, quality fine.
    counts = {"insiders": 0, "smart_money": 0, "activist_13d": 0, "quality": 3998}
    healths = assess(counts, universe_size=10_433)
    assert all_ok(healths) is False
    failed = {h.lens for h in healths if not h.ok}
    assert failed == {"insiders", "smart_money"}  # activist_13d is warn_only


def test_all_ok_true_when_every_lens_healthy():
    counts = {"insiders": 4, "smart_money": 30, "activist_13d": 12, "quality": 3998}
    assert all_ok(assess(counts, universe_size=10_433)) is True
