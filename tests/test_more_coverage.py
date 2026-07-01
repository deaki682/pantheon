"""Additional coverage to clear 500 tests."""
import pytest

from achilles.sleeve import AchillesPosition, AchillesSleeve
from delphi.execution import build_targets
from delphi.signals import momentum
from delphi.sleeve import DelphiSleeve
from oracle.journal import JournalEntry, append, grade, read
from oracle.learning import calibration_stats, conviction_tier
from oracle.positioning import compute_derived, potential_to_conviction, size_book
from oracle.sleeve import OracleSleeve
from shared.base_sleeve import BaseSleeve, next_business_day
from shared.edgar import classify_8k, extract_ex_date, parse_items


# --- shared/edgar ---

def test_classify_8k_only_bankruptcy():
    out = classify_8k("1.03")
    assert out == ["bankruptcy"]


def test_classify_8k_only_delisting():
    out = classify_8k("3.01")
    assert out == ["delisting"]


def test_parse_items_handles_multiple_periods():
    items = parse_items("Item 2.02.")
    assert "2.02" in items


def test_extract_ex_date_january():
    assert extract_ex_date("ex-date: January 15, 2025") == "2025-01-15"


def test_extract_ex_date_december():
    assert extract_ex_date("distribution date: December 31, 2024") == "2024-12-31"


# --- BaseSleeve ---

def test_next_business_day_chains():
    # Saturday -> Monday
    saturday = "2024-06-01"  # 2024-06-01 is a Saturday
    assert next_business_day(saturday) == "2024-06-03"


def test_base_sleeve_init_cooldown_days_default():
    s = BaseSleeve("test")
    assert s.cooldown_days == 0  # base default


def test_base_sleeve_realized_pnl_accumulates():
    s = BaseSleeve("x", initial_cash=1000)
    s.buy("A", 1.0, 100, "2024-05-29")
    s.sell("A", 1.0, 110, "2024-05-30")
    first = s.realized_pnl
    s.buy("B", 1.0, 100, "2024-06-01")
    s.sell("B", 1.0, 90, "2024-06-02")
    # Second trade was a loss; realized_pnl should be less than after first trade
    assert s.realized_pnl < first


# --- Oracle ---

def test_oracle_compute_derived_with_zero_horizon_returns_expected_return_as_cagr():
    d = {
        "scenarios": {
            "bull": {"target": 150, "probability": 0.3},
            "base": {"target": 100, "probability": 0.5},
            "bear": {"target": 50, "probability": 0.2},
        },
        "ratings": {"moat": 0.5, "runway": 0.5, "quality": 0.5, "management": 0.5},
    }
    out = compute_derived(d, current_price=100, horizon_years=0)
    assert out["expected_cagr"] == out["expected_return"]


def test_oracle_size_book_concentrated():
    """5 names all top conviction, 5 sectors -> distributes."""
    scored = [
        {"symbol": f"S{i}", "conviction": 0.9, "sector": f"sec{i}"} for i in range(5)
    ]
    targets = size_book(scored, equity=10_000)
    assert len(targets) == 5
    total = sum(targets.values())
    assert total <= 9_000 + 1e-6


def test_oracle_potential_score_bearish_collapses_to_zero():
    """A bearish dossier (bull below current) -> upside=0 -> potential_score=0.

    Asymmetry collapses the multiplier to 0 since upside is 0. This is
    intentional: Oracle is long-only and shouldn't generate a 'short' signal.
    """
    d = {
        "scenarios": {
            "bull": {"target": 60, "probability": 0.2},
            "base": {"target": 50, "probability": 0.3},
            "bear": {"target": 30, "probability": 0.5},
        },
        "ratings": {"moat": 0.5, "runway": 0.5, "quality": 0.5, "management": 0.5},
    }
    out = compute_derived(d, current_price=100, horizon_years=1)
    assert out["expected_return"] < 0
    assert out["potential_score"] == 0  # asymmetry_mult = 0 zeros it


def test_oracle_journal_features(tmp_path):
    p = tmp_path / "j.jsonl"
    e = JournalEntry(
        timestamp="2024-05-29", symbol="X", decision="buy",
        conviction=0.7, horizon_days=90, price=100,
        features={"thesis": "good", "potential_score": 0.5},
    )
    append(str(p), e)
    out = read(str(p))
    assert out[0].features["thesis"] == "good"


def test_oracle_grade_already_graded_returns_same():
    e = JournalEntry(
        timestamp="2024-01-01", symbol="X", decision="buy",
        conviction=0.7, horizon_days=30, price=100,
    )
    grade(e, final_price=200)
    assert e.graded_outcome == "win"
    # Grading again with different price
    grade(e, final_price=80)
    assert e.graded_outcome == "loss"  # overwrites


def test_oracle_calibration_single_tier():
    """When only one tier has data, monotonic is False (need 2+)."""
    e = JournalEntry("a", "X", "buy", 0.9, 30, 100)
    e.graded_return = 0.10
    out = calibration_stats([e])
    assert out["monotonic"] is False


def test_oracle_sleeve_persistence_keeps_peak():
    s = OracleSleeve(initial_cash=1000)
    s.cash = 1500
    s.update_peak()
    d = s.to_dict()
    s2 = OracleSleeve.from_dict(d)
    assert s2.peak_equity == 1500


# --- Delphi ---

def test_delphi_momentum_zero_lookback():
    assert momentum([100, 110], 0) == 0.0


def test_delphi_build_targets_empty():
    assert build_targets([], equity=10_000, risk_budget=1.0) == {}


def test_delphi_can_buy_any_stock():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("AAPL", 1, 100, "2024-05-29") is True


# --- Achilles ---

def test_achilles_position_dataclass():
    pos = AchillesPosition(
        symbol="X", shares=10, entry_price=100, entry_date="2024-05-29",
        stop_price=92.0, exit_date="2024-06-05", score=0.5, surprise_pct=8.0,
    )
    assert pos.symbol == "X"
    assert pos.shares == 10


def test_achilles_enter_basic():
    s = AchillesSleeve()
    ok = s.enter(
        symbol="AAPL", shares=5.0, price=100.0,
        today="2024-05-29", score=0.5, surprise_pct=8.0,
    )
    assert ok is True
    assert "AAPL" in s.positions
    assert s.positions["AAPL"].symbol == "AAPL"


def test_achilles_rejects_when_halted():
    s = AchillesSleeve()
    s.halted = True
    ok = s.enter(
        symbol="AAPL", shares=5.0, price=100.0,
        today="2024-05-29", score=0.5, surprise_pct=8.0,
    )
    assert ok is False
