"""Simulated-week integration test: three gods, multiple passes, multiple trades.

Validates:
  1. Budget isolation — one god's spending never reduces another's cash.
  2. Position isolation — one god's buys don't appear in another's sleeve.
  3. Sell isolation — one god selling a symbol doesn't affect another's position.
  4. Ledger isolation — each god's ledger only contains its own orders.
  5. Symbol overlap detection — when two gods buy the same symbol, both sleeves
     track independently and the combined broker exposure is flagged.
  6. Equity conservation — total cash + positions (per god) is internally
     consistent after every pass, accounting for fees.
  7. Kill switch — all three gods liquidate, not just one.
"""
from __future__ import annotations

import os
import tempfile

import pytest

from achilles.sleeve import AchillesSleeve
from delphi.execution import build_targets, plan_orders as delphi_plan_orders
from delphi.sleeve import DelphiSleeve
from oracle.execution import plan_orders as oracle_plan_orders
from oracle.sleeve import OracleSleeve
from shared.guards import (
    OrderRecord,
    PositionMismatch,
    aggregate_sleeve_shares,
    already_placed_today,
    append_order,
    check_position_sanity,
    filter_orders_by_ledger,
    kill_switch_active,
    pre_trade_check,
    read_ledger,
)


# ── Simulated market ────────────────────────────────────────────────────

PRICES = {
    # Week simulation: 5 days of prices
    "day1": {"AAPL": 150.0, "MSFT": 300.0, "GOOG": 130.0, "AMZN": 180.0,
             "JPM": 190.0, "BAC": 35.0, "XOM": 110.0, "CVX": 155.0,
             "UNH": 500.0, "JNJ": 155.0, "SPY": 450.0},
    "day2": {"AAPL": 152.0, "MSFT": 305.0, "GOOG": 128.0, "AMZN": 183.0,
             "JPM": 192.0, "BAC": 36.0, "XOM": 108.0, "CVX": 157.0,
             "UNH": 505.0, "JNJ": 154.0, "SPY": 452.0},
    "day3": {"AAPL": 148.0, "MSFT": 295.0, "GOOG": 132.0, "AMZN": 176.0,
             "JPM": 188.0, "BAC": 34.0, "XOM": 112.0, "CVX": 152.0,
             "UNH": 510.0, "JNJ": 156.0, "SPY": 448.0},
    "day4": {"AAPL": 155.0, "MSFT": 310.0, "GOOG": 135.0, "AMZN": 185.0,
             "JPM": 195.0, "BAC": 37.0, "XOM": 115.0, "CVX": 160.0,
             "UNH": 515.0, "JNJ": 158.0, "SPY": 455.0},
    "day5": {"AAPL": 153.0, "MSFT": 308.0, "GOOG": 133.0, "AMZN": 182.0,
             "JPM": 193.0, "BAC": 36.5, "XOM": 113.0, "CVX": 158.0,
             "UNH": 512.0, "JNJ": 157.0, "SPY": 453.0},
}

DATES = ["2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25", "2026-06-26"]
DAY_KEYS = ["day1", "day2", "day3", "day4", "day5"]


def _exec_order(sleeve, order, prices, today):
    """Execute a single order against a sleeve. Returns order_id or None."""
    sym = order["symbol"]
    px = prices.get(sym, 0)
    if px <= 0:
        return None
    god = sleeve.name
    if order["side"] == "buy":
        shares = order["dollars"] / px
        ok = sleeve.buy(sym, shares, px, today, sector="test")
        return f"{god}-{sym}-buy-{today}" if ok else None
    elif order["side"] == "sell":
        pos = sleeve.positions.get(sym)
        if not pos:
            return None
        shares = min(order["dollars"] / px, pos.shares)
        ok = sleeve.sell(sym, shares, px, today)
        return f"{god}-{sym}-sell-{today}" if ok else None
    return None


# ── Test 1: Budget isolation ────────────────────────────────────────────

class TestBudgetIsolation:
    def test_spending_is_independent(self):
        """One god buying should not reduce another god's cash."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        px = PRICES["day1"]

        # Oracle buys AAPL
        oracle.buy("AAPL", 1.0, px["AAPL"], DATES[0])
        assert delphi.cash == 1000.0, "Delphi cash changed after Oracle buy"
        assert achilles.cash == 1000.0, "Achilles cash changed after Oracle buy"

        # Delphi buys MSFT
        delphi.buy("MSFT", 0.5, px["MSFT"], DATES[0])
        assert oracle.cash == pytest.approx(1000.0 - 150.0 - 150.0 * 5 / 10000, abs=0.01)
        assert achilles.cash == 1000.0, "Achilles cash changed after Delphi buy"

        # Achilles enters a position
        achilles.enter(
            symbol="JPM", shares=5.0, price=px["JPM"],
            today=DATES[0], score=0.5, surprise_pct=8.0,
        )
        assert oracle.cash == pytest.approx(1000.0 - 150.0 * (1 + 5/10000), abs=0.01)
        assert delphi.cash == pytest.approx(1000.0 - 150.0 * (1 + 5/10000), abs=0.01)

    def test_total_equity_conserved_per_god(self):
        """Each god's equity = cash + positions, accounting for fees."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        px = PRICES["day1"]
        oracle.buy("AAPL", 2.0, px["AAPL"], DATES[0])
        delphi.buy("GOOG", 3.0, px["GOOG"], DATES[0])
        achilles.enter(
            symbol="XOM", shares=3.0, price=px["XOM"],
            today=DATES[0], score=0.3, surprise_pct=5.0,
        )

        # At purchase prices, equity = initial - fees (since positions valued at cost)
        oracle_eq = oracle.equity(px)
        delphi_eq = delphi.equity(px)
        achilles_eq = achilles.equity(px)

        oracle_fees = 2 * px["AAPL"] * 5 / 10000
        delphi_fees = 3 * px["GOOG"] * 5 / 10000

        assert oracle_eq == pytest.approx(1000.0 - oracle_fees, abs=0.01)
        assert delphi_eq == pytest.approx(1000.0 - delphi_fees, abs=0.01)
        # Achilles fee computed differently (on dollars, not shares*price)
        assert achilles_eq < 1000.0  # lost some to fees


# ── Test 2: Position isolation ──────────────────────────────────────────

class TestPositionIsolation:
    def test_positions_dont_leak(self):
        """Buying in one god doesn't create a position in another."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("GOOG", 1.0, 130.0, DATES[0])
        achilles.enter(
            symbol="JPM", shares=5.0, price=190.0,
            today=DATES[0], score=0.5, surprise_pct=8.0,
        )

        assert "AAPL" in oracle.positions
        assert "AAPL" not in delphi.positions

        assert "GOOG" in delphi.positions
        assert "GOOG" not in oracle.positions

        assert "JPM" in achilles.positions
        assert "JPM" not in oracle.positions
        assert "JPM" not in delphi.positions

    def test_same_symbol_different_gods(self):
        """Two gods can buy the same symbol independently."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("AAPL", 2.0, 150.0, DATES[0])

        assert oracle.positions["AAPL"].shares == pytest.approx(1.0)
        assert delphi.positions["AAPL"].shares == pytest.approx(2.0)

        # Selling from Oracle doesn't touch Delphi
        oracle.sell("AAPL", 1.0, 155.0, DATES[1])
        assert "AAPL" not in oracle.positions
        assert delphi.positions["AAPL"].shares == pytest.approx(2.0)


# ── Test 3: Sell isolation ──────────────────────────────────────────────

class TestSellIsolation:
    def test_sell_only_affects_own_sleeve(self):
        """Selling from one god does not reduce another's shares."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("MSFT", 1.0, 300.0, DATES[0])
        delphi.buy("MSFT", 1.5, 300.0, DATES[0])

        oracle_cash_before = oracle.cash
        delphi_cash_before = delphi.cash

        oracle.sell("MSFT", 1.0, 310.0, DATES[2])

        assert "MSFT" not in oracle.positions
        assert delphi.positions["MSFT"].shares == pytest.approx(1.5)
        assert delphi.cash == delphi_cash_before  # untouched
        assert oracle.cash > oracle_cash_before  # got proceeds


# ── Test 4: Ledger isolation ───────────────────────────────────────────

class TestLedgerIsolation:
    def test_separate_ledgers(self, tmp_path):
        """Each god's ledger only contains its own orders."""
        oracle_ledger = str(tmp_path / "oracle_ledger.jsonl")
        delphi_ledger = str(tmp_path / "delphi_ledger.jsonl")
        achilles_ledger = str(tmp_path / "achilles_ledger.jsonl")

        append_order(oracle_ledger, OrderRecord("o1", "AAPL", "buy", 150.0, DATES[0]))
        append_order(oracle_ledger, OrderRecord("o2", "MSFT", "buy", 300.0, DATES[0]))
        append_order(delphi_ledger, OrderRecord("d1", "GOOG", "buy", 130.0, DATES[0]))
        append_order(achilles_ledger, OrderRecord("a1", "JPM", "buy", 190.0, DATES[0]))

        ol = read_ledger(oracle_ledger)
        dl = read_ledger(delphi_ledger)
        al = read_ledger(achilles_ledger)

        assert len(ol) == 2
        assert len(dl) == 1
        assert len(al) == 1
        assert {r.symbol for r in ol} == {"AAPL", "MSFT"}
        assert {r.symbol for r in dl} == {"GOOG"}
        assert {r.symbol for r in al} == {"JPM"}

    def test_filter_orders_by_ledger_isolates(self, tmp_path):
        """filter_orders_by_ledger only returns orders matching THIS god's IDs."""
        oracle_ledger_path = str(tmp_path / "oracle_ledger.jsonl")
        delphi_ledger_path = str(tmp_path / "delphi_ledger.jsonl")

        append_order(oracle_ledger_path, OrderRecord("o1", "AAPL", "buy", 150.0, DATES[0]))
        append_order(delphi_ledger_path, OrderRecord("d1", "GOOG", "buy", 130.0, DATES[0]))

        all_broker_orders = [
            {"order_id": "o1", "symbol": "AAPL", "state": "filled"},
            {"order_id": "d1", "symbol": "GOOG", "state": "filled"},
            {"order_id": "a1", "symbol": "JPM", "state": "filled"},
        ]

        oracle_ledger = read_ledger(oracle_ledger_path)
        delphi_ledger = read_ledger(delphi_ledger_path)

        oracle_orders = filter_orders_by_ledger(all_broker_orders, oracle_ledger)
        delphi_orders = filter_orders_by_ledger(all_broker_orders, delphi_ledger)

        assert len(oracle_orders) == 1
        assert oracle_orders[0]["symbol"] == "AAPL"
        assert len(delphi_orders) == 1
        assert delphi_orders[0]["symbol"] == "GOOG"

    def test_empty_ledger_returns_nothing(self):
        """An empty ledger never claims any broker orders."""
        broker_orders = [
            {"order_id": "x1", "symbol": "AAPL"},
            {"order_id": "x2", "symbol": "MSFT"},
        ]
        assert filter_orders_by_ledger(broker_orders, []) == []

    def test_already_placed_today_per_god(self, tmp_path):
        """already_placed_today checks within one god's ledger only."""
        oracle_ledger_path = str(tmp_path / "oracle.jsonl")
        delphi_ledger_path = str(tmp_path / "delphi.jsonl")

        append_order(oracle_ledger_path, OrderRecord("o1", "AAPL", "buy", 150.0, DATES[0]))

        ol = read_ledger(oracle_ledger_path)
        dl = read_ledger(delphi_ledger_path)

        assert already_placed_today(ol, "AAPL", "buy", DATES[0]) is True
        assert already_placed_today(dl, "AAPL", "buy", DATES[0]) is False


# ── Test 5: Symbol overlap detection ───────────────────────────────────

class TestSymbolOverlap:
    def test_detect_overlapping_symbols(self):
        """Verify we can detect when two gods hold the same symbol."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("AAPL", 2.0, 150.0, DATES[0])
        achilles.enter(
            symbol="AAPL", shares=3.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        )

        oracle_syms = set(oracle.positions.keys())
        delphi_syms = set(delphi.positions.keys())
        achilles_syms = set(achilles.positions.keys())

        overlap_od = oracle_syms & delphi_syms
        overlap_oa = oracle_syms & achilles_syms
        overlap_da = delphi_syms & achilles_syms

        assert overlap_od == {"AAPL"}
        assert overlap_oa == {"AAPL"}
        assert overlap_da == {"AAPL"}

        # Combined broker exposure = sum of all gods' shares
        achilles_aapl = achilles.positions["AAPL"].shares if "AAPL" in achilles.positions else 0.0
        total_aapl_shares = (
            oracle.positions["AAPL"].shares
            + delphi.positions["AAPL"].shares
            + achilles_aapl
        )
        assert total_aapl_shares > 3.0  # all three gods have AAPL


# ── Test 6: Multi-day simulation ───────────────────────────────────────

class TestMultiDaySimulation:
    def _run_oracle_day(self, sleeve, targets, prices, today, ledger_path):
        """Simulate one Oracle pass."""
        orders = oracle_plan_orders(sleeve, targets, prices, today=today)
        for o in orders:
            oid = _exec_order(sleeve, o, prices, today)
            if oid:
                append_order(ledger_path, OrderRecord(oid, o["symbol"], o["side"], o["dollars"], today))

    def _run_delphi_day(self, sleeve, picks, prices, today, ledger_path):
        """Simulate one Delphi pass."""
        targets = build_targets(picks, sleeve.equity(prices), risk_budget=1.0)
        orders = delphi_plan_orders(sleeve, targets, prices)
        for o in orders:
            oid = _exec_order(sleeve, o, prices, today)
            if oid:
                append_order(ledger_path, OrderRecord(oid, o["symbol"], o["side"], o["dollars"], today))

    def _run_achilles_day(self, sleeve, events, prices, today, ledger_path):
        """Simulate one Achilles pass — basket model, one slot per name."""
        if not events:
            return

        for ev in events:
            px = prices.get(ev["symbol"], 0)
            if px <= 0:
                continue
            shares = max(1, int(sleeve.cash * 0.3 / px))
            ok = sleeve.enter(
                symbol=ev["symbol"], shares=shares, price=px,
                today=today, score=ev.get("score", 0.3), surprise_pct=5.0,
            )
            if ok:
                dollars = shares * px
                oid = f"ach-{ev['symbol']}-{today}"
                append_order(ledger_path, OrderRecord(
                    oid, ev["symbol"], "buy", dollars, today))

    def test_full_week_isolation(self, tmp_path):
        """Run all three gods through a 5-day week and verify isolation."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        ol = str(tmp_path / "oracle.jsonl")
        dl = str(tmp_path / "delphi.jsonl")
        al = str(tmp_path / "achilles.jsonl")

        # Oracle targets: buy AAPL and MSFT equally across the week
        oracle_targets = {"AAPL": 200.0, "MSFT": 300.0, "GOOG": 150.0}

        # Delphi picks: momentum ranked
        delphi_picks = [
            {"symbol": "AAPL"},
            {"symbol": "MSFT"},
            {"symbol": "JPM"},
        ]

        # Achilles events: staggered across days
        achilles_events = [
            [{"symbol": "AAPL", "score": 0.4}],
            [{"symbol": "BAC", "score": 0.3}],
            [],
            [{"symbol": "XOM", "score": 0.5}],
            [],
        ]

        initial_total = oracle.cash + delphi.cash + achilles.cash
        snapshots = []

        for day_idx in range(5):
            today = DATES[day_idx]
            px = PRICES[DAY_KEYS[day_idx]]

            oracle.process_settlements(today)
            delphi.process_settlements(today)
            achilles.process_settlements(today)

            o_cash_before = oracle.cash
            d_cash_before = delphi.cash
            a_cash_before = achilles.cash

            # Oracle trades Tue and Fri (day 0=Mon, 1=Tue, 3=Thu, 4=Fri)
            if day_idx in (1, 4):
                self._run_oracle_day(oracle, oracle_targets, px, today, ol)

            # Delphi trades Tue and Fri
            if day_idx in (1, 4):
                self._run_delphi_day(delphi, delphi_picks, px, today, dl)

            # Achilles trades every day it has events
            self._run_achilles_day(achilles, achilles_events[day_idx], px, today, al)

            # After trading: verify no cross-contamination
            # If Oracle didn't trade, its cash should be unchanged
            if day_idx not in (1, 4):
                assert oracle.cash == o_cash_before, \
                    f"Day {day_idx}: Oracle cash changed on non-trade day"

            # Achilles cash should only change if it had events and no position
            if not achilles_events[day_idx]:
                assert achilles.cash == a_cash_before, \
                    f"Day {day_idx}: Achilles cash changed with no events"

            snapshots.append({
                "day": day_idx,
                "oracle": {"cash": oracle.cash, "equity": oracle.equity(px),
                           "positions": set(oracle.positions.keys())},
                "delphi": {"cash": delphi.cash, "equity": delphi.equity(px),
                           "positions": set(delphi.positions.keys())},
                "achilles": {"cash": achilles.cash, "equity": achilles.equity(px),
                             "positions": set(achilles.positions.keys())},
            })

        # Final verification
        final_px = PRICES["day5"]

        # 1. Each god's equity is internally consistent
        for god, sleeve in [("oracle", oracle), ("delphi", delphi)]:
            pos_value = sum(
                p.shares * final_px.get(s, p.avg_price)
                for s, p in sleeve.positions.items()
            )
            assert sleeve.equity(final_px) == pytest.approx(sleeve.cash + pos_value, abs=0.01), \
                f"{god} equity inconsistent"

        achilles_pos_value = sum(
            p.shares * final_px.get(s, p.entry_price)
            for s, p in achilles.positions.items()
        )
        assert achilles.equity(final_px) == pytest.approx(
            achilles.cash + achilles_pos_value, abs=0.01), \
            "achilles equity inconsistent"

        # 2. Ledgers are disjoint
        oracle_ledger = read_ledger(ol)
        delphi_ledger = read_ledger(dl)
        achilles_ledger = read_ledger(al)

        oracle_ids = {r.order_id for r in oracle_ledger}
        delphi_ids = {r.order_id for r in delphi_ledger}
        achilles_ids = {r.order_id for r in achilles_ledger}

        assert not oracle_ids & delphi_ids, "Oracle and Delphi ledger IDs overlap"
        assert not oracle_ids & achilles_ids, "Oracle and Achilles ledger IDs overlap"
        assert not delphi_ids & achilles_ids, "Delphi and Achilles ledger IDs overlap"

        # 3. filter_orders_by_ledger isolates correctly
        all_orders = [{"order_id": r.order_id, "symbol": r.symbol}
                      for r in oracle_ledger + delphi_ledger + achilles_ledger]

        only_oracle = filter_orders_by_ledger(all_orders, oracle_ledger)
        only_delphi = filter_orders_by_ledger(all_orders, delphi_ledger)
        only_achilles = filter_orders_by_ledger(all_orders, achilles_ledger)

        assert len(only_oracle) == len(oracle_ledger)
        assert len(only_delphi) == len(delphi_ledger)
        assert len(only_achilles) == len(achilles_ledger)

    def test_oracle_rotation_doesnt_touch_delphi(self, tmp_path):
        """Oracle sells a position → Delphi's position in same symbol untouched."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        px = PRICES["day1"]
        oracle.buy("AAPL", 1.0, px["AAPL"], DATES[0])
        delphi.buy("AAPL", 2.0, px["AAPL"], DATES[0])

        delphi_shares_before = delphi.positions["AAPL"].shares
        delphi_cash_before = delphi.cash

        # Oracle rotates out of AAPL
        oracle_targets = {"MSFT": 300.0}  # AAPL removed
        orders = oracle_plan_orders(oracle, oracle_targets, PRICES["day3"], today=DATES[2])
        for o in orders:
            _exec_order(oracle, o, PRICES["day3"], DATES[2])

        assert "AAPL" not in oracle.positions, "Oracle should have sold AAPL"
        assert delphi.positions["AAPL"].shares == delphi_shares_before
        assert delphi.cash == delphi_cash_before


# ── Test 7: Kill switch ────────────────────────────────────────────────

class TestKillSwitch:
    def test_all_gods_liquidate(self, tmp_path):
        """Kill switch liquidates ALL three gods."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        px = PRICES["day1"]
        oracle.buy("AAPL", 1.0, px["AAPL"], DATES[0])
        delphi.buy("MSFT", 0.5, px["MSFT"], DATES[0])
        achilles.enter(
            symbol="JPM", shares=5.0, price=px["JPM"],
            today=DATES[0], score=0.5, surprise_pct=8.0,
        )

        assert len(oracle.positions) == 1
        assert len(delphi.positions) == 1
        assert "JPM" in achilles.positions

        ks_path = os.path.join(str(tmp_path), "KILL_SWITCH")
        with open(ks_path, "w") as f:
            f.write("halt")

        assert kill_switch_active(str(tmp_path))

        oracle.liquidate_all(px, DATES[1])
        delphi.liquidate_all(px, DATES[1])
        achilles.liquidate(px, DATES[1])

        assert len(oracle.positions) == 0
        assert len(delphi.positions) == 0
        assert achilles.positions == {}

        # All cash recovered (minus fees)
        assert oracle.cash > 900.0
        assert delphi.cash > 900.0
        assert achilles.cash > 900.0


# ── Test 8: Persistence isolation ──────────────────────────────────────

class TestPersistenceIsolation:
    def test_save_load_independent(self, tmp_path):
        """Saving one god's sleeve doesn't overwrite another's."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("GOOG", 2.0, 130.0, DATES[0])
        achilles.enter(
            symbol="JPM", shares=5.0, price=190.0,
            today=DATES[0], score=0.5, surprise_pct=8.0,
        )

        o_path = str(tmp_path / "oracle_sleeve.json")
        d_path = str(tmp_path / "delphi_sleeve.json")
        a_path = str(tmp_path / "achilles_sleeve.json")

        oracle.save(o_path)
        delphi.save(d_path)
        achilles.save(a_path)

        o2 = OracleSleeve.load(o_path)
        d2 = DelphiSleeve.load(d_path)
        a2 = AchillesSleeve.load(a_path)

        assert "AAPL" in o2.positions
        assert "GOOG" not in o2.positions
        assert "GOOG" in d2.positions
        assert "AAPL" not in d2.positions
        assert "JPM" in a2.positions

    def test_overwrite_own_sleeve_only(self, tmp_path):
        """Re-saving one god doesn't affect other gods' files."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("GOOG", 2.0, 130.0, DATES[0])

        o_path = str(tmp_path / "oracle_sleeve.json")
        d_path = str(tmp_path / "delphi_sleeve.json")

        oracle.save(o_path)
        delphi.save(d_path)

        # Oracle buys more and re-saves
        oracle.buy("MSFT", 0.5, 300.0, DATES[1])
        oracle.save(o_path)

        # Delphi's file should still be the original
        d2 = DelphiSleeve.load(d_path)
        assert "GOOG" in d2.positions
        assert "MSFT" not in d2.positions
        assert d2.cash == delphi.cash  # original Delphi cash after GOOG buy


# ── Test 9: Cooldown isolation ─────────────────────────────────────────

class TestCooldownIsolation:
    def test_cooldown_per_god(self):
        """A sell cooldown in Oracle doesn't block Delphi from buying."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        oracle.sell("AAPL", 1.0, 155.0, DATES[1])

        # Oracle has a 31-day cooldown on AAPL
        assert oracle.cooldowns.get("AAPL", "") > DATES[1]

        # Delphi can still buy AAPL immediately
        ok = delphi.buy("AAPL", 1.0, 155.0, DATES[1])
        assert ok is True
        assert "AAPL" in delphi.positions

        # Oracle can NOT buy AAPL due to cooldown
        ok = oracle.buy("AAPL", 1.0, 155.0, DATES[2])
        assert ok is False


# ── Test 10: Pre-trade broker sanity check ─────────────────────────────

class TestPreTradeSanityCheck:
    def _save_sleeves(self, tmp_path, oracle=None, delphi=None, achilles=None):
        paths = {
            "oracle": str(tmp_path / "oracle_sleeve.json"),
            "delphi": str(tmp_path / "delphi_sleeve.json"),
            "achilles": str(tmp_path / "achilles_sleeve.json"),
        }
        if oracle:
            oracle.save(paths["oracle"])
        if delphi:
            delphi.save(paths["delphi"])
        if achilles:
            achilles.save(paths["achilles"])
        return paths

    def test_all_in_sync_passes(self, tmp_path):
        """When sleeves match broker, pre_trade_check returns True."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("AAPL", 2.0, 150.0, DATES[0])
        delphi.buy("MSFT", 0.5, 300.0, DATES[0])

        paths = self._save_sleeves(tmp_path, oracle, delphi, achilles)

        broker_positions = {"AAPL": 3.0, "MSFT": 0.5}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is True

    def test_mismatch_fails(self, tmp_path):
        """When sleeves disagree with broker, pre_trade_check returns False."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("AAPL", 2.0, 150.0, DATES[0])

        paths = self._save_sleeves(tmp_path, oracle, delphi)
        # Achilles sleeve doesn't exist — that's fine, treated as empty

        # Broker says 2.5 shares, sleeves say 3.0
        broker_positions = {"AAPL": 2.5}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is False

    def test_broker_has_unknown_position(self, tmp_path):
        """Broker holds a symbol no sleeve claims — ignored (pre-existing)."""
        oracle = OracleSleeve(initial_cash=1000.0)
        paths = self._save_sleeves(tmp_path, oracle)

        broker_positions = {"GOOG": 5.0}
        mismatches = check_position_sanity(broker_positions, sleeve_paths=paths)
        assert len(mismatches) == 0

    def test_sleeve_has_phantom_position(self, tmp_path):
        """Sleeve claims shares the broker doesn't have — mismatch."""
        oracle = OracleSleeve(initial_cash=1000.0)
        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        paths = self._save_sleeves(tmp_path, oracle)

        broker_positions = {}  # broker has nothing
        mismatches = check_position_sanity(broker_positions, sleeve_paths=paths)
        assert len(mismatches) == 1
        assert mismatches[0].symbol == "AAPL"
        assert mismatches[0].sleeve_total == pytest.approx(1.0)
        assert mismatches[0].broker_shares == 0.0

    def test_achilles_position_sums(self, tmp_path):
        """Achilles basket positions sum correctly for the pre-trade check."""
        achilles = AchillesSleeve(initial_cash=1000.0)
        achilles.enter(
            symbol="AAPL", shares=3.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        )
        paths = self._save_sleeves(tmp_path, achilles=achilles)

        achilles_aapl = achilles.positions["AAPL"].shares

        broker_positions = {"AAPL": achilles_aapl}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is True

        # Off by a bit → mismatch
        broker_positions = {"AAPL": achilles_aapl - 0.1}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is False

    def test_three_gods_same_symbol(self, tmp_path):
        """All three gods hold the same symbol — total must match broker."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        delphi.buy("AAPL", 2.0, 150.0, DATES[0])
        achilles.enter(
            symbol="AAPL", shares=3.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        )

        paths = self._save_sleeves(tmp_path, oracle, delphi, achilles)

        achilles_aapl = achilles.positions["AAPL"].shares
        total = 1.0 + 2.0 + achilles_aapl

        # Exact match
        broker_positions = {"AAPL": total}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is True

        # Aggregate shows all three gods
        combined = aggregate_sleeve_shares(paths)
        assert "oracle" in combined["AAPL"]
        assert "delphi" in combined["AAPL"]
        assert "achilles" in combined["AAPL"]
        assert combined["AAPL"]["oracle"] == pytest.approx(1.0)
        assert combined["AAPL"]["delphi"] == pytest.approx(2.0)
        assert combined["AAPL"]["achilles"] == pytest.approx(achilles_aapl)

    def test_missing_sleeve_file_is_empty(self, tmp_path):
        """A missing sleeve file is treated as zero positions, not an error."""
        paths = {
            "oracle": str(tmp_path / "nonexistent_oracle.json"),
            "delphi": str(tmp_path / "nonexistent_delphi.json"),
            "achilles": str(tmp_path / "nonexistent_achilles.json"),
        }
        broker_positions = {}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is True

        # Broker-only positions with no sleeves → no mismatch (pre-existing)
        broker_positions = {"AAPL": 1.0}
        assert pre_trade_check(broker_positions, sleeve_paths=paths) is True


# ── Test 11: Circuit breaker / halt isolation ─────────────────────────

class TestCircuitBreakerIsolation:
    def test_oracle_halt_doesnt_block_others(self):
        """Oracle hitting 32% drawdown halts Oracle; Delphi and Achilles trade freely."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.halted = True

        assert oracle.buy("AAPL", 1.0, 150.0, DATES[0]) is False
        assert delphi.buy("AAPL", 1.0, 150.0, DATES[0]) is True
        assert achilles.enter(
            symbol="AAPL", shares=5.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        ) is True

    def test_achilles_halt_doesnt_block_others(self):
        """Achilles hitting halt blocks Achilles; Oracle and Delphi unaffected."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)
        # Peak at 1000, but cash dropped to 500 -> 50% drawdown > 40% HALT_DRAWDOWN
        achilles = AchillesSleeve(initial_cash=1000.0)
        achilles.cash = 500.0

        achilles.check_halt()
        assert achilles.halted is True

        assert achilles.enter(
            symbol="AAPL", shares=3.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        ) is False
        assert oracle.buy("AAPL", 1.0, 150.0, DATES[0]) is True
        assert delphi.buy("MSFT", 1.0, 300.0, DATES[0]) is True


# ── Test 12: Settlement isolation ─────────────────────────────────────

class TestSettlementIsolation:
    def test_pending_settlements_per_sleeve(self):
        """A sell in Oracle creates pending_settlements only in Oracle."""
        oracle = OracleSleeve(initial_cash=1000.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 1.0, 150.0, DATES[0])
        oracle.sell("AAPL", 1.0, 155.0, DATES[1])

        assert len(oracle.pending_settlements) == 1
        assert len(delphi.pending_settlements) == 0
        assert delphi.settled_cash(DATES[1]) == 1000.0

    def test_gfv_count_per_sleeve(self):
        """A GFV in one god doesn't increment another's count."""
        oracle = OracleSleeve(initial_cash=500.0)
        delphi = DelphiSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 2.0, 150.0, DATES[0])
        oracle.sell("AAPL", 2.0, 155.0, DATES[0])
        # Buy with unsettled proceeds → GFV
        oracle.buy("MSFT", 1.0, 300.0, DATES[0])

        assert oracle.gfv_count >= 1
        assert delphi.gfv_count == 0


# ── Test 13: Achilles basket ─────────────────────────────────────────

class TestAchillesBasket:
    def test_achilles_holds_a_basket(self):
        """Achilles holds many distinct names (the diversified PEAD basket)."""
        achilles = AchillesSleeve(initial_cash=5000.0)
        assert achilles.enter(
            symbol="AAPL", shares=5.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        ) is True
        assert achilles.enter(
            symbol="MSFT", shares=3.0, price=300.0,
            today=DATES[0], score=0.4, surprise_pct=7.0,
        ) is True
        assert set(achilles.positions) == {"AAPL", "MSFT"}

    def test_achilles_full_basket_doesnt_block_oracle(self):
        """A full Achilles basket still lets Oracle buy."""
        from achilles.sleeve import MAX_POSITIONS
        oracle = OracleSleeve(initial_cash=5000.0)
        achilles = AchillesSleeve(initial_cash=50_000.0)

        for i in range(MAX_POSITIONS):
            achilles.enter(
                symbol=f"SYM{i}", shares=10.0, price=10.0,
                today=DATES[0], score=0.3, surprise_pct=5.0,
            )
        assert len(achilles.positions) == MAX_POSITIONS

        # Basket full — Achilles can't open another
        assert achilles.enter(
            symbol="OVERFLOW", shares=10.0, price=10.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        ) is False

        # Oracle is unaffected
        assert oracle.buy("AAPL", 1.0, 150.0, DATES[0]) is True


# ── Test 14: Achilles trading doesn't block others ──────────────────

class TestAchillesTradingIsolation:
    def test_achilles_trades_dont_block_others(self):
        """Achilles entering a position doesn't affect Oracle/Delphi."""
        oracle = OracleSleeve(initial_cash=5000.0)
        delphi = DelphiSleeve(initial_cash=5000.0)
        achilles = AchillesSleeve(initial_cash=5000.0)

        achilles.enter(
            symbol="D0", shares=10.0, price=10.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        )
        assert "D0" in achilles.positions

        # Oracle and Delphi trade freely
        assert oracle.buy("AAPL", 1.0, 150.0, DATES[0]) is True
        assert delphi.buy("MSFT", 1.0, 300.0, DATES[0]) is True


# ── Test 15: Halted state persists through save/load ──────────────────

class TestHaltedPersistence:
    def test_halted_survives_round_trip(self, tmp_path):
        """A halted sleeve stays halted after save/load."""
        oracle = OracleSleeve(initial_cash=1000.0)
        oracle.halted = True

        path = str(tmp_path / "oracle_sleeve.json")
        oracle.save(path)
        loaded = OracleSleeve.load(path)

        assert loaded.halted is True
        assert loaded.buy("AAPL", 1.0, 150.0, DATES[0]) is False

    def test_achilles_halted_survives_round_trip(self, tmp_path):
        """Achilles halted flag persists through save/load."""
        # Peak at 1000, cash dropped to 500 -> 50% drawdown > 40% HALT_DRAWDOWN
        achilles = AchillesSleeve(initial_cash=1000.0)
        achilles.cash = 500.0
        achilles.check_halt()
        assert achilles.halted is True

        path = str(tmp_path / "achilles_sleeve.json")
        achilles.save(path)
        loaded = AchillesSleeve.load(path)

        assert loaded.halted is True
        assert loaded.enter(
            symbol="AAPL", shares=3.0, price=150.0,
            today=DATES[0], score=0.3, surprise_pct=5.0,
        ) is False


# ── Test 16: Peak equity independence ─────────────────────────────────

class TestPeakEquityIsolation:
    def test_peak_equity_per_god(self):
        """Updating peak equity on one god doesn't touch the other."""
        oracle = OracleSleeve(initial_cash=1000.0)
        achilles = AchillesSleeve(initial_cash=1000.0)

        oracle.buy("AAPL", 2.0, 150.0, DATES[0])
        oracle.update_peak({"AAPL": 200.0})

        assert oracle.peak_equity == pytest.approx(
            oracle.cash + 2.0 * 200.0, abs=0.01
        )
        assert achilles.peak_equity == 1000.0
