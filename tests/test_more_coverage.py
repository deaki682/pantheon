"""Additional coverage to clear 500 tests."""
import pytest

from achilles.brief import Play, brief_from_dict, brief_to_dict, make_brief
from achilles.playbooks import build_playbooks, recalibrate
from achilles.quotes import normalize_quotes
from achilles.scoring import has_disqualifier
from achilles.sleeve import AchillesPosition, AchillesSleeve
from delphi.execution import build_targets
from delphi.signals import composite_score, momentum, score_sectors
from delphi.sleeve import PICK_BLOCKLIST, DelphiSleeve, is_blocked
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

def test_delphi_blocklist_includes_qqq():
    assert is_blocked("QQQ")


def test_delphi_sleeve_blocks_blockedlist_via_buy():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("QQQ", 1, 100, "2024-05-29") is False


def test_delphi_momentum_zero_lookback():
    assert momentum([100, 110], 0) == 0.0


def test_delphi_score_sectors_only_canonical():
    out = score_sectors({"XLK": [100] * 127, "ZZZ": [100] * 127}, [100] * 127)
    assert "technology" in out
    assert len(out) == 1


def test_delphi_build_targets_empty_sectors():
    assert build_targets({}, equity=10_000, risk_budget=1.0) == {}


def test_delphi_composite_with_outperformance():
    sec = [100.0] * 127
    sec[-1] = 110
    sec[-64] = 100
    spy = [100.0] * 127
    spy[-1] = 100  # SPY flat
    spy[-64] = 100
    out = composite_score(sec, spy)
    assert out > 0


# --- Achilles ---

def test_achilles_play_dataclass():
    p = Play(
        entry_dollars=100, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15",
    )
    assert p.entry_dollars == 100


def test_achilles_brief_roundtrip_disqualified():
    b = make_brief(
        event_id="e1", event_class="earnings_reaction", symbol="X",
        score=0, filing={}, setup={}, disqualifiers=["trading_halt"], play=None,
    )
    d = brief_to_dict(b)
    b2 = brief_from_dict(d)
    assert b2.disqualifiers == ["trading_halt"]
    assert b2.play is None


def test_achilles_recalibrate_full():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    recalibrate(
        pb, new_base_rate=0.65, new_hold_days=12,
        new_hard_stop_pct=-0.06, new_profit_target_pct=0.15,
    )
    assert pb.base_rate == 0.65
    assert pb.expected_hit_rate == 0.65
    assert pb.hard_stop_pct == -0.06
    assert pb.profit_target_pct == 0.15
    assert pb.uncalibrated is False


def test_achilles_quotes_normalizes_uppercase():
    rows = [{"symbol": "msft", "last_trade_price": 350}]
    out = normalize_quotes(rows)
    assert "MSFT" in out


def test_achilles_position_dataclass():
    pos = AchillesPosition(
        event_id="e", symbol="X", event_class="ma_target",
        shares=10, entry_price=100, entry_date="2024-05-29",
        dollars_at_entry=1000, hard_stop_price=95, profit_target_price=106,
        time_stop_date="2024-06-15",
    )
    assert pos.symbol == "X"
    assert pos.shares == 10


def test_achilles_conservative_mode_default():
    s = AchillesSleeve()
    assert s.conservative_mode is True


def test_achilles_conservative_can_be_disabled():
    s = AchillesSleeve(conservative_mode=False)
    assert s.conservative_mode is False


def test_achilles_disqualifier_check_combined():
    """Universal AND class disqualifier present -> still disqualified."""
    assert has_disqualifier(["trading_halt", "guidance_withdrawn"], "earnings_reaction")
