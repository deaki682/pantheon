"""Tests for proteus.sleeve.LiveBook — the live discretionary book."""
import pytest

from proteus.journal import JournalError
from proteus.sleeve import LiveBook, CONCENTRATION_ACK_PCT, HALT_DRAWDOWN

_ACK = ("Worst case the thesis is wrong and this convex name draws down ~35% to its "
        "asset floor; that is survivable at this size and the conviction earns the bet.")


def _funded(amount=1968.05):
    book = LiveBook(pending_funding={"from": "midas"})
    book.fund(amount=amount, source="midas", date="2026-07-06")
    return book


def test_unfunded_book_refuses_entries():
    book = LiveBook(pending_funding={"from": "midas"})
    with pytest.raises(JournalError):
        book.enter(symbol="XYZ", shares=1, price=10.0, date="2026-07-06",
                   spy_price=745.0, horizon_days=5, confidence=0.6,
                   edge_class="forced_flow")


def test_funding_clears_pending_and_sets_cash():
    book = _funded(1968.05)
    assert book.is_funded()
    assert book.pending_funding is None
    assert book.cash == pytest.approx(1968.05)
    assert book.contributed_cash == pytest.approx(1968.05)


def test_fund_rejects_nonpositive():
    book = LiveBook()
    with pytest.raises(JournalError):
        book.fund(amount=0, source="midas", date="2026-07-06")


def test_enter_is_long_only_by_construction():
    book = _funded()
    pos = book.enter(symbol="xyz", shares=10, price=20.0, date="2026-07-06",
                     spy_price=745.0, horizon_days=10, confidence=0.55,
                     edge_class="event_catalyst")
    assert pos.side == "long"
    assert book.cash == pytest.approx(1968.05 - 200.0)
    # LiveBook.enter has no side parameter at all
    with pytest.raises(TypeError):
        book.enter(symbol="abc", side="short", shares=1, price=5.0,
                   date="2026-07-06", spy_price=745.0, horizon_days=5,
                   confidence=0.5, edge_class="short_thesis")


def test_no_leverage_and_one_position_per_symbol():
    book = _funded(100.0)
    with pytest.raises(JournalError):
        book.enter(symbol="BIG", shares=100, price=10.0, date="2026-07-06",
                   spy_price=745.0, horizon_days=5, confidence=0.5,
                   edge_class="value")
    # 5 * $10 = $50 = 50% of a $100 book: past the concentration line, so it
    # needs an ack (see the dedicated concentration tests below).
    book.enter(symbol="OK", shares=5, price=10.0, date="2026-07-06",
               spy_price=745.0, horizon_days=5, confidence=0.5,
               edge_class="value", risk_ack=_ACK)
    with pytest.raises(JournalError):
        book.enter(symbol="OK", shares=1, price=10.0, date="2026-07-06",
                   spy_price=745.0, horizon_days=5, confidence=0.5,
                   edge_class="value", risk_ack=_ACK)


def test_small_position_needs_no_ack():
    # A position at/under the concentration line enters freely, no ack.
    book = _funded(1000.0)
    dollars = CONCENTRATION_ACK_PCT * 1000.0 - 1.0   # just under the line
    book.enter(symbol="SM", shares=dollars / 10.0, price=10.0, date="2026-07-06",
               spy_price=745.0, horizon_days=5, confidence=0.5, edge_class="value")
    assert "SM" in book.positions


def test_concentration_past_line_requires_ack():
    book = _funded(1000.0)
    # 40% of the book, no ack -> refused.
    with pytest.raises(JournalError):
        book.enter(symbol="BIG", shares=40, price=10.0, date="2026-07-06",
                   spy_price=745.0, horizon_days=5, confidence=0.7, edge_class="value")
    # a too-thin ack is still refused
    with pytest.raises(JournalError):
        book.enter(symbol="BIG", shares=40, price=10.0, date="2026-07-06",
                   spy_price=745.0, horizon_days=5, confidence=0.7,
                   edge_class="value", risk_ack="yolo")


def test_all_in_allowed_with_conscious_ack():
    # The experiment CAN go all-in — greed is fine, unconscious greed is not.
    book = _funded(1000.0)
    book.enter(symbol="CONV", shares=100, price=10.0, date="2026-07-06",
               spy_price=745.0, horizon_days=30, confidence=0.85,
               edge_class="special_situation", risk_ack=_ACK)
    assert book.cash == pytest.approx(0.0)
    assert book.positions["CONV"].dollars == pytest.approx(1000.0)


def test_drawdown_breaker_halts_new_entries_without_liquidating():
    book = _funded(1000.0)
    book.enter(symbol="HELD", shares=100, price=10.0, date="2026-07-06",
               spy_price=745.0, horizon_days=60, confidence=0.8,
               edge_class="value", risk_ack=_ACK)
    # mark it down 45% -> past the 40% breaker
    marks = {"HELD": 5.5, "SPY": 745.0}
    assert book.absolute_drawdown(marks) >= HALT_DRAWDOWN
    assert book.check_halt(marks) is True
    assert book.halted
    # the existing position is NOT force-sold — it plays out to its kill
    assert "HELD" in book.positions
    # but no new entry is allowed while halted
    book.cash = 500.0  # pretend some cash freed up
    with pytest.raises(JournalError):
        book.enter(symbol="NEW", shares=1, price=10.0, date="2026-07-07",
                   spy_price=745.0, horizon_days=5, confidence=0.5, edge_class="value")


def test_peak_equity_survives_roundtrip(tmp_path):
    path = str(tmp_path / "proteus_sleeve.json")
    book = _funded(1000.0)
    book.update_peak({})
    book.save(path)
    loaded = LiveBook.load(path)
    assert loaded.peak_equity == pytest.approx(1000.0)


def test_exit_records_real_fill_no_modeled_fees():
    book = _funded(1000.0)
    book.enter(symbol="ABC", shares=10, price=50.0, date="2026-07-06",
               spy_price=700.0, horizon_days=10, confidence=0.6,
               edge_class="momentum", risk_ack=_ACK)  # $500 = 50% -> ack
    trade = book.exit(symbol="ABC", price=55.0, date="2026-07-10",
                      spy_price=707.0, exit_reason="exit_plan")
    assert trade.net_return == pytest.approx(0.10)
    assert trade.spy_return == pytest.approx(0.01)
    assert trade.excess == pytest.approx(0.09)
    assert book.cash == pytest.approx(1000.0 - 500.0 + 550.0)
    assert book.realized_pnl == pytest.approx(50.0)


def test_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "proteus_sleeve.json")
    book = _funded(500.0)
    book.enter(symbol="RT", shares=4, price=25.0, date="2026-07-06",
               spy_price=745.0, horizon_days=30, confidence=0.7,
               edge_class="special_situation")
    book.save(path)
    loaded = LiveBook.load(path)
    assert loaded.cash == pytest.approx(book.cash)
    assert loaded.contributed_cash == pytest.approx(500.0)
    assert "RT" in loaded.positions
    assert loaded.positions["RT"].shares == pytest.approx(4)
    assert loaded.is_funded()


def test_sleeve_json_visible_to_guards(tmp_path, monkeypatch):
    """filter_broker_to_gods must see Proteus positions once saved."""
    import os
    from shared.guards import _load_sleeve_shares
    path = str(tmp_path / "proteus_sleeve.json")
    book = _funded(500.0)
    book.enter(symbol="GRD", shares=3, price=10.0, date="2026-07-06",
               spy_price=745.0, horizon_days=5, confidence=0.5,
               edge_class="value")
    book.save(path)
    shares = _load_sleeve_shares(path)
    assert shares == {"GRD": pytest.approx(3.0)}


def test_kill_switch_liquidation():
    book = _funded(1000.0)
    book.enter(symbol="KS", shares=10, price=20.0, date="2026-07-06",
               spy_price=700.0, horizon_days=30, confidence=0.6,
               edge_class="value")
    sold = book.liquidate_all({"KS": 18.0, "SPY": 690.0}, "2026-07-08")
    assert sold == [("KS", 10, 18.0)]
    assert book.halted
    assert not book.positions
    assert book.closed[-1].exit_reason == "kill_switch"


def test_horizon_expiry():
    book = _funded(1000.0)
    book.enter(symbol="HZ", shares=1, price=100.0, date="2026-07-06",
               spy_price=700.0, horizon_days=3, confidence=0.5,
               edge_class="momentum")
    assert book.horizon_expired("2026-07-08") == []
    assert book.horizon_expired("2026-07-09") == ["HZ"]


def test_proteus_is_live_env_gate():
    from shared.guards import is_live
    assert is_live("proteus", {"PROTEUS_LIVE": "true"})
    assert not is_live("proteus", {"PROTEUS_LIVE": "false"})
    assert not is_live("proteus", {})
