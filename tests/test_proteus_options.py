"""Tests for Proteus v2 long-option accounting + chain glue (2026-07-11).

Covers the three build-precondition gaps from cache/proteus_playbook.md:
(a) option positions living honestly in the sleeve/journal, (b) the
chain-pricing glue math, (c) the validator making the playbook's entry
gates mechanical.
"""
import json

import pytest

from proteus.journal import JournalError, validate_decision
from proteus.options import (
    CATALYST_EXPIRY_BUFFER_DAYS,
    MULTIPLIER,
    SPREAD_JUSTIFY_PCT,
    breakeven_move_pct,
    contract_mid,
    expiry_clears_catalyst,
    occ_symbol,
    priced_read,
    spread_pct,
)
from proteus.sleeve import CONCENTRATION_ACK_PCT, LiveBook

_ACK = ("Worst case this contract expires worthless and the full net debit is "
        "gone; that is sized as an acceptable, journaled outcome and the "
        "conviction earns the concentration.")

_EDGE_MATH = ("p(thesis)=0.45 vs chain-implied ~0.22; straddle prices a 6.1% move, "
              "I expect ~14% on the ruling; breakeven needs +8.3%; half-wrong still "
              "clears the debit.")


def _funded(amount=2500.0):
    book = LiveBook(pending_funding={"from": "treasury"})
    book.fund(amount=amount, source="treasury", date="2026-07-13")
    return book


def _enter_kwargs(**over):
    kw = dict(underlying="XYZ", option_type="call", strike=50.0,
              expiration="2026-10-16", contracts=2, premium=1.50,
              date="2026-07-13", spy_price=755.0, catalyst_date="2026-09-15",
              horizon_days=95, confidence=0.6, edge_class="event_catalyst")
    kw.update(over)
    return kw


# ---------------------------------------------------------------- glue math

def test_occ_symbol_format():
    assert occ_symbol("spy", "2026-09-18", "call", 760) == "SPY260918C00760000"
    assert occ_symbol("XYZ", "2026-10-16", "put", 12.5) == "XYZ261016P00012500"
    with pytest.raises(ValueError):
        occ_symbol("XYZ", "2026-10-16", "straddle", 12.5)


def test_spread_pct_math_and_edge_cases():
    assert spread_pct(0.95, 1.05) == pytest.approx(0.10 / 1.00)
    assert spread_pct(None, 1.0) is None
    assert spread_pct(1.10, 1.00) is None      # crossed market is not a number
    assert spread_pct(0.0, 0.0) is None


def test_breakeven_move_pct_call_and_put():
    # call: spot 100, strike 105, premium 2 -> needs +7%
    assert breakeven_move_pct(100.0, 105.0, "call", 2.0) == pytest.approx(0.07)
    # put: spot 100, strike 95, premium 2 -> needs -7%
    assert breakeven_move_pct(100.0, 95.0, "put", 2.0) == pytest.approx(-0.07)
    assert breakeven_move_pct(0, 95.0, "put", 2.0) is None


def test_contract_mid_precedence():
    assert contract_mid(0.90, 1.10, mark=1.05) == pytest.approx(1.05)
    assert contract_mid(0.90, 1.10) == pytest.approx(1.00)
    assert contract_mid(None, None, last=0.75) == pytest.approx(0.75)
    assert contract_mid(None, None) is None


def test_expiry_clears_catalyst_boundary():
    assert expiry_clears_catalyst("2026-09-15", "2026-09-29")       # exactly 14d
    assert not expiry_clears_catalyst("2026-09-15", "2026-09-28")   # 13d — too tight
    assert CATALYST_EXPIRY_BUFFER_DAYS == 14


def test_priced_read_produces_journal_arithmetic():
    r = priced_read(spot=100.0, atm_call_mid=3.0, atm_put_mid=3.0,
                    my_expected_move_pct=0.14, direction=1,
                    strike=105.0, option_type="call", premium=2.0,
                    bid=1.90, ask=2.10)
    assert r["priced_move_pct"] == pytest.approx(0.06)      # straddle/spot
    assert r["edge_vs_priced_pct"] == pytest.approx(0.08)
    assert r["breakeven_move_pct"] == pytest.approx(0.07)
    assert r["spread_pct"] == pytest.approx(0.10)
    # exactly at the line is NOT past it
    assert r["spread_needs_justification"] is (0.10 > SPREAD_JUSTIFY_PCT)


# ---------------------------------------------------------------- journal

def _option_record(**over):
    rec = {
        "date": "2026-07-13", "action": "enter", "instrument": "option",
        "symbol": "XYZ261016C00050000", "side": "long",
        "dollars": 300.0, "price": 1.50, "spy_price": 755.0,
        "horizon_days": 95, "confidence": 0.6, "edge_class": "event_catalyst",
        "underlying": "XYZ", "option_type": "call", "strike": 50.0,
        "expiration": "2026-10-16", "contracts": 2, "max_loss": 300.0,
        "catalyst_date": "2026-09-15", "edge_arithmetic": _EDGE_MATH,
        "thesis": "T" * 200, "falsifiable_prediction": "P" * 80,
        "exit_plan": "E" * 40, "kill_condition": "K" * 20,
    }
    rec.update(over)
    return rec


def test_journal_accepts_valid_option_enter():
    assert validate_decision(_option_record()) is not None


def test_journal_refuses_option_stub_fields():
    for missing in ("underlying", "option_type", "strike", "expiration",
                    "contracts", "max_loss", "catalyst_date", "edge_arithmetic"):
        rec = _option_record()
        del rec[missing]
        with pytest.raises(JournalError):
            validate_decision(rec)


def test_journal_refuses_non_long_option():
    with pytest.raises(JournalError):
        validate_decision(_option_record(side="short"))


def test_journal_refuses_bad_instrument():
    with pytest.raises(JournalError):
        validate_decision(_option_record(instrument="swap"))


def test_journal_enforces_catalyst_expiry_buffer():
    # catalyst 2026-10-10, expiry 2026-10-16: only 6 days of buffer
    with pytest.raises(JournalError):
        validate_decision(_option_record(catalyst_date="2026-10-10"))


def test_journal_enforces_debit_and_max_loss_consistency():
    with pytest.raises(JournalError):
        validate_decision(_option_record(dollars=250.0))          # != 2*1.50*100
    with pytest.raises(JournalError):
        validate_decision(_option_record(max_loss=150.0))         # != net debit


def test_journal_refuses_thin_edge_arithmetic():
    with pytest.raises(JournalError):
        validate_decision(_option_record(edge_arithmetic="cheap vol, feels good"))


def test_journal_option_exit_allows_worthless_expiry_price_zero():
    rec = {"date": "2026-10-16", "action": "exit", "instrument": "option",
           "symbol": "XYZ261016C00050000", "price": 0.0, "spy_price": 760.0,
           "exit_reason": "horizon_expiry"}
    assert validate_decision(rec) is not None
    # equities keep the strictly-positive rule
    with pytest.raises(JournalError):
        validate_decision({"date": "2026-10-16", "action": "exit",
                           "symbol": "XYZ", "price": 0.0, "spy_price": 760.0,
                           "exit_reason": "exit_plan"})


# ---------------------------------------------------------------- sleeve

def test_enter_option_deducts_debit_and_bounds_loss():
    book = _funded(2500.0)
    pos = book.enter_option(**_enter_kwargs())        # 2 * 1.50 * 100 = $300
    assert book.cash == pytest.approx(2200.0)
    assert pos.cost == pytest.approx(300.0)
    assert pos.max_loss == pytest.approx(300.0)       # invariant 1, at entry
    assert pos.occ == "XYZ261016C00050000"


def test_enter_option_gates():
    unfunded = LiveBook(pending_funding={"from": "treasury"})
    with pytest.raises(JournalError):
        unfunded.enter_option(**_enter_kwargs())
    book = _funded(2500.0)
    book.halted = True
    with pytest.raises(JournalError):
        book.enter_option(**_enter_kwargs())
    book.halted = False
    with pytest.raises(JournalError):                  # debit exceeds cash
        book.enter_option(**_enter_kwargs(contracts=100))
    with pytest.raises(JournalError):                  # fractional contracts
        book.enter_option(**_enter_kwargs(contracts=1.5))
    book.enter_option(**_enter_kwargs())
    with pytest.raises(JournalError):                  # one position per contract
        book.enter_option(**_enter_kwargs())


def test_enter_option_concentration_needs_ack():
    book = _funded(1000.0)
    # 3 * $1.50 * 100 = $450 = 45% of the book -> past the line, no ack -> refused
    with pytest.raises(JournalError):
        book.enter_option(**_enter_kwargs(contracts=3))
    book.enter_option(**_enter_kwargs(contracts=3, risk_ack=_ACK))
    assert book.cash == pytest.approx(550.0)
    assert CONCENTRATION_ACK_PCT == pytest.approx(0.25)


def test_open_option_forces_live_marks_on_next_entry():
    """The stale-equity bug guard extends to options: with an option open,
    the concentration denominator must be live (marks or equity=)."""
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())
    with pytest.raises(JournalError):
        book.enter(symbol="NEW", shares=10, price=10.0, date="2026-07-14",
                   spy_price=755.0, horizon_days=5, confidence=0.5,
                   edge_class="value")
    book.enter(symbol="NEW", shares=10, price=10.0, date="2026-07-14",
               spy_price=755.0, horizon_days=5, confidence=0.5,
               edge_class="value", marks={"XYZ261016C00050000": 1.50})
    assert "NEW" in book.positions


def test_exit_option_accounting_and_realized_pnl():
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())               # $300 debit
    trade = book.exit_option(occ="XYZ261016C00050000", premium=2.25,
                             date="2026-09-20", spy_price=770.1,
                             exit_reason="exit_plan")
    assert trade.net_return == pytest.approx(0.50)     # 2.25/1.50 - 1
    assert trade.proceeds == pytest.approx(450.0)
    assert trade.spy_return == pytest.approx(0.02)
    assert trade.excess == pytest.approx(0.48)
    assert book.cash == pytest.approx(2500.0 - 300.0 + 450.0)
    assert book.realized_pnl == pytest.approx(150.0)


def test_worthless_expiry_is_total_bounded_loss():
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())
    trade = book.exit_option(occ="XYZ261016C00050000", premium=0.0,
                             date="2026-10-16", spy_price=755.0,
                             exit_reason="horizon_expiry")
    assert trade.net_return == pytest.approx(-1.0)
    assert book.cash == pytest.approx(2200.0)          # the debit is gone, nothing more
    assert book.realized_pnl == pytest.approx(-300.0)


def test_expired_options_listing():
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())
    assert book.expired_options("2026-10-15") == []
    assert book.expired_options("2026-10-16") == ["XYZ261016C00050000"]


def test_equity_marks_options_by_occ():
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())               # cash 2200, cost 300
    assert book.equity({}) == pytest.approx(2500.0)    # falls back to entry premium
    assert book.equity({"XYZ261016C00050000": 3.0}) == pytest.approx(2200.0 + 600.0)


def test_save_load_roundtrip_with_options(tmp_path):
    path = str(tmp_path / "proteus_sleeve.json")
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())
    book.exit_option(occ="XYZ261016C00050000", premium=2.0, date="2026-09-20",
                     spy_price=760.0, exit_reason="exit_plan")
    book.enter_option(**_enter_kwargs(option_type="put", strike=45.0))
    book.save(path)
    loaded = LiveBook.load(path)
    assert loaded.cash == pytest.approx(book.cash)
    assert "XYZ261016P00045000" in loaded.option_positions
    assert loaded.option_positions["XYZ261016P00045000"].max_loss == pytest.approx(300.0)
    assert len(loaded.closed_options) == 1
    assert loaded.closed_options[0].net_return == pytest.approx(2.0 / 1.5 - 1)
    # trades_count counts option round-trips too (dashboard stat)
    assert json.load(open(path))["trades_count"] == 1


def test_option_positions_invisible_to_equity_share_guards(tmp_path):
    """filter_broker_to_gods reads `positions` as broker EQUITY shares; an
    OCC contract must never leak into that map."""
    from shared.guards import _load_sleeve_shares
    path = str(tmp_path / "proteus_sleeve.json")
    book = _funded(2500.0)
    book.enter_option(**_enter_kwargs())
    book.save(path)
    assert _load_sleeve_shares(path) == {}


def test_kill_switch_liquidates_options_too():
    book = _funded(2500.0)
    book.enter(symbol="EQ", shares=10, price=20.0, date="2026-07-13",
               spy_price=755.0, horizon_days=30, confidence=0.6,
               edge_class="value")
    book.enter_option(**_enter_kwargs(marks={"EQ": 20.0}))
    sold = book.liquidate_all({"EQ": 19.0, "XYZ261016C00050000": 1.20,
                               "SPY": 750.0}, "2026-07-20")
    assert ("EQ", 10, 19.0) in sold
    assert ("XYZ261016C00050000", 2, 1.20) in sold
    assert not book.positions and not book.option_positions
    assert book.halted
    assert book.closed_options[-1].exit_reason == "kill_switch"
