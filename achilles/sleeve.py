"""AchillesSleeve — event-keyed, standalone (NOT a BaseSleeve).

Positions are keyed by event_id, not by symbol. The same stock can carry
two simultaneous Achilles positions if it generated two distinct events.

Each position has its own absolute-dollar hard stop, absolute-dollar
profit target, and calendar time-stop date.

Sticky $600 hard floor: at 40% drawdown or when equity <= $600, halt
permanently until a manual reset.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Optional


HARD_FLOOR = 600.0
DRAWDOWN_HALT = 0.40
MAX_CONCURRENT_POSITIONS = 8
MAX_TRADES_PER_DAY = 5
MIN_SCORE_TO_OPEN = 0.05
PER_POSITION_CAP_FRAC = 0.10
PER_POSITION_MIN = 100.0
PER_POSITION_MAX = 400.0
CONSERVATIVE_HALVE = 0.5
FEE_BPS = 5  # 5 basis points


def _to_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def next_business_day(today: str) -> str:
    d = _to_date(today)
    while True:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            return d.strftime("%Y-%m-%d")


@dataclass
class AchillesPosition:
    event_id: str
    symbol: str
    event_class: str
    shares: float
    entry_price: float
    entry_date: str
    dollars_at_entry: float
    hard_stop_price: float
    profit_target_price: float
    time_stop_date: str
    score: float = 0.0
    trail_armed_at: float = 0.0  # 0 means no trailing
    trail_pct: float = 0.0
    high_water_price: float = 0.0


@dataclass
class Settlement:
    settle_date: str
    amount: float


class AchillesSleeve:
    """Standalone sleeve — does NOT inherit from BaseSleeve."""

    def __init__(self, initial_cash: float = 1_000.0, conservative_mode: bool = True):
        self.name = "achilles"
        self.cash = float(initial_cash)
        self.positions: dict[str, AchillesPosition] = {}
        self.pending_settlements: list[Settlement] = []
        self.realized_pnl: float = 0.0
        self.gfv_count: int = 0
        self.trades_count: int = 0
        self.halted: bool = False
        self.contributed_cash: float = float(initial_cash)
        self.peak_equity: float = float(initial_cash)
        self.conservative_mode: bool = conservative_mode
        self._trades_today_date: str = ""
        self._trades_today: int = 0

    # ------- accounting -------

    def inject(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("inject() requires non-negative amount")
        self.cash += amount
        self.contributed_cash += amount

    def equity(self, marks: Optional[dict[str, float]] = None) -> float:
        marks = marks or {}
        total = self.cash
        for p in self.positions.values():
            total += p.shares * marks.get(p.symbol, p.entry_price)
        return total

    def update_peak(self, marks: Optional[dict[str, float]] = None) -> None:
        eq = self.equity(marks)
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: Optional[dict[str, float]] = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        eq = self.equity(marks)
        return max(0.0, 1.0 - eq / self.peak_equity)

    def check_hard_floor(self, marks: Optional[dict[str, float]] = None) -> bool:
        """Returns True iff the sleeve hit its floor and is now halted."""
        eq = self.equity(marks)
        if eq <= HARD_FLOOR + 1e-9 or self.absolute_drawdown(marks) >= DRAWDOWN_HALT - 1e-9:
            self.halted = True
            return True
        return False

    def manual_reset(self) -> None:
        """Operator-only: clears the halted flag."""
        self.halted = False

    def unsettled_cash(self, today: str) -> float:
        return sum(s.amount for s in self.pending_settlements if s.settle_date > today)

    def settled_cash(self, today: str) -> float:
        return self.cash - self.unsettled_cash(today)

    def process_settlements(self, today: str) -> None:
        self.pending_settlements = [s for s in self.pending_settlements if s.settle_date > today]

    # ------- daily counter -------

    def _ensure_today(self, today: str) -> None:
        if self._trades_today_date != today:
            self._trades_today_date = today
            self._trades_today = 0

    def trades_today(self, today: str) -> int:
        self._ensure_today(today)
        return self._trades_today

    # ------- position sizing -------

    def position_dollars(self, score: float) -> float:
        """Compute the absolute-dollar entry size from sleeve equity and score.

        cap = 10% of equity, clamped to [$100, $400]. Halved in conservative mode.
        """
        cap = PER_POSITION_CAP_FRAC * self.equity()
        cap = max(PER_POSITION_MIN, min(PER_POSITION_MAX, cap))
        if self.conservative_mode:
            cap *= CONSERVATIVE_HALVE
        return float(cap)

    # ------- open / close -------

    def open(
        self,
        *,
        event_id: str,
        symbol: str,
        event_class: str,
        entry_price: float,
        score: float,
        hard_stop_price: float,
        profit_target_price: float,
        time_stop_date: str,
        today: str,
        trail_armed_at: float = 0.0,
        trail_pct: float = 0.0,
    ) -> Optional[AchillesPosition]:
        """Open a position. Returns the position on success, None on rejection."""
        if self.halted:
            return None
        if score < MIN_SCORE_TO_OPEN:
            return None
        if entry_price <= 0:
            return None
        if event_id in self.positions:
            return None
        if len(self.positions) >= MAX_CONCURRENT_POSITIONS:
            return None
        self._ensure_today(today)
        if self._trades_today >= MAX_TRADES_PER_DAY:
            return None

        dollars = self.position_dollars(score)
        if dollars <= 0 or dollars > self.cash + 1e-9:
            return None
        fee = dollars * FEE_BPS / 10_000
        total_cost = dollars + fee
        if total_cost > self.cash + 1e-9:
            return None
        if total_cost > self.settled_cash(today) + 1e-9:
            self.gfv_count += 1
        shares = dollars / entry_price
        pos = AchillesPosition(
            event_id=event_id,
            symbol=symbol.upper(),
            event_class=event_class,
            shares=shares,
            entry_price=entry_price,
            entry_date=today,
            dollars_at_entry=dollars,
            hard_stop_price=hard_stop_price,
            profit_target_price=profit_target_price,
            time_stop_date=time_stop_date,
            score=score,
            trail_armed_at=trail_armed_at,
            trail_pct=trail_pct,
            high_water_price=entry_price,
        )
        self.positions[event_id] = pos
        self.cash -= total_cost
        self.trades_count += 1
        self._trades_today += 1
        return pos

    def close(
        self, event_id: str, *, exit_price: float, today: str,
    ) -> Optional[float]:
        """Close a position at the given exit price. Returns realized PnL or None."""
        pos = self.positions.get(event_id)
        if pos is None:
            return None
        if exit_price <= 0:
            return None
        proceeds = pos.shares * exit_price
        fee = proceeds * FEE_BPS / 10_000
        net = proceeds - fee
        realized = net - pos.dollars_at_entry
        self.realized_pnl += realized
        self.cash += net
        self.pending_settlements.append(Settlement(next_business_day(today), net))
        del self.positions[event_id]
        self.trades_count += 1
        return realized

    def liquidate_all(self, marks: dict[str, float], today: str) -> list[tuple[str, str, float]]:
        """Kill-switch path: close every position at the given marks. Bypasses halted."""
        out: list[tuple[str, str, float]] = []
        was_halted = self.halted
        self.halted = False
        try:
            for eid in list(self.positions.keys()):
                pos = self.positions[eid]
                px = marks.get(pos.symbol, pos.entry_price)
                realized = self.close(eid, exit_price=px, today=today)
                if realized is not None:
                    out.append((eid, pos.symbol, realized))
        finally:
            self.halted = was_halted
        return out

    # ------- persistence -------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cash": self.cash,
            "positions": {k: asdict(v) for k, v in self.positions.items()},
            "pending_settlements": [asdict(s) for s in self.pending_settlements],
            "realized_pnl": self.realized_pnl,
            "gfv_count": self.gfv_count,
            "trades_count": self.trades_count,
            "halted": self.halted,
            "contributed_cash": self.contributed_cash,
            "peak_equity": self.peak_equity,
            "conservative_mode": self.conservative_mode,
            "trades_today_date": self._trades_today_date,
            "trades_today": self._trades_today,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AchillesSleeve":
        s = cls(initial_cash=0.0, conservative_mode=bool(data.get("conservative_mode", True)))
        s.cash = float(data["cash"])
        s.positions = {k: AchillesPosition(**v) for k, v in data.get("positions", {}).items()}
        s.pending_settlements = [Settlement(**x) for x in data.get("pending_settlements", [])]
        s.realized_pnl = float(data.get("realized_pnl", 0.0))
        s.gfv_count = int(data.get("gfv_count", 0))
        s.trades_count = int(data.get("trades_count", 0))
        s.halted = bool(data.get("halted", False))
        s.contributed_cash = float(data.get("contributed_cash", s.cash))
        s.peak_equity = float(data.get("peak_equity", s.cash))
        s._trades_today_date = data.get("trades_today_date", "")
        s._trades_today = int(data.get("trades_today", 0))
        return s

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: str) -> "AchillesSleeve":
        with open(path) as f:
            return cls.from_dict(json.load(f))
