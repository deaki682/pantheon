"""MidasSleeve — single-position, all-in weekly sleeve.

At most ONE position at any time. Enter Monday, exit Friday or on stop.
Standalone (does NOT inherit BaseSleeve or AchillesSleeve).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Optional


CAPITAL_BASE = 1_000.0
CAPITAL_CEILING = 12_000.0
HARD_STOP_PCT = -0.10
HALT_DRAWDOWN = 0.40
FEE_BPS = 5
STOP_COOLDOWN_WEEKS = 4


def _to_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def next_business_day(today: str) -> str:
    d = _to_date(today)
    while True:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            return d.strftime("%Y-%m-%d")


@dataclass
class MidasPosition:
    symbol: str
    shares: float
    entry_price: float
    entry_date: str
    stop_price: float
    exit_date: str
    score: float
    convergence_count: int
    signals: dict = field(default_factory=dict)


@dataclass
class WeeklyResult:
    symbol: str
    week_id: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    exit_reason: str
    return_pct: float
    pnl: float
    score: float
    convergence_count: int
    signals: dict = field(default_factory=dict)


@dataclass
class Settlement:
    settle_date: str
    amount: float


class MidasSleeve:
    """Single-position all-in sleeve. At most one position at a time."""

    def __init__(self, initial_cash: float = CAPITAL_BASE):
        self.name = "midas"
        self.cash: float = float(initial_cash)
        self.position: Optional[MidasPosition] = None
        self.peak_equity: float = float(initial_cash)
        self.realized_pnl: float = 0.0
        self.trades_count: int = 0
        self.halted: bool = False
        self.contributed_cash: float = float(initial_cash)
        self.pending_settlements: list[Settlement] = []
        self.gfv_count: int = 0
        self.cooldowns: dict[str, str] = {}
        self.weekly_results: list[WeeklyResult] = []

    # ------- accounting -------

    def equity(self, marks: Optional[dict[str, float]] = None) -> float:
        marks = marks or {}
        total = self.cash
        if self.position:
            px = marks.get(self.position.symbol, self.position.entry_price)
            total += self.position.shares * px
        return total

    def update_peak(self, marks: Optional[dict[str, float]] = None) -> None:
        eq = self.equity(marks)
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: Optional[dict[str, float]] = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks) / self.peak_equity)

    def check_halt(self, marks: Optional[dict[str, float]] = None) -> bool:
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    def inject(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("inject() requires non-negative amount")
        self.cash += amount
        self.contributed_cash += amount

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("withdraw() requires non-negative amount")
        if amount > self.cash + 1e-9:
            raise ValueError("withdraw exceeds available cash")
        self.cash -= amount
        self.contributed_cash -= amount

    def unsettled_cash(self, today: str) -> float:
        return sum(s.amount for s in self.pending_settlements if s.settle_date > today)

    def settled_cash(self, today: str) -> float:
        return self.cash - self.unsettled_cash(today)

    def process_settlements(self, today: str) -> None:
        self.pending_settlements = [
            s for s in self.pending_settlements if s.settle_date > today
        ]

    def in_cooldown(self, symbol: str, today: str) -> bool:
        until = self.cooldowns.get(symbol.upper())
        if not until:
            return False
        return today < until

    # ------- trading -------

    def enter(
        self,
        *,
        symbol: str,
        shares: float,
        price: float,
        today: str,
        score: float,
        convergence_count: int,
        signals: dict,
        exit_date: str,
    ) -> bool:
        if self.halted:
            return False
        if self.position is not None:
            return False
        if shares <= 0 or price <= 0:
            return False
        if self.in_cooldown(symbol, today):
            return False

        dollars = shares * price
        fee = dollars * FEE_BPS / 10_000
        total_cost = dollars + fee
        if total_cost > self.cash + 1e-9:
            return False

        if total_cost > self.settled_cash(today) + 1e-9:
            self.gfv_count += 1

        stop_price = round(price * (1.0 + HARD_STOP_PCT), 4)

        self.position = MidasPosition(
            symbol=symbol.upper(),
            shares=shares,
            entry_price=price,
            entry_date=today,
            stop_price=stop_price,
            exit_date=exit_date,
            score=score,
            convergence_count=convergence_count,
            signals=dict(signals),
        )
        self.cash -= total_cost
        self.trades_count += 1
        return True

    def exit(self, *, price: float, today: str, reason: str) -> Optional[float]:
        if self.position is None:
            return None
        if price <= 0:
            return None

        pos = self.position
        proceeds = pos.shares * price
        fee = proceeds * FEE_BPS / 10_000
        net = proceeds - fee
        cost = pos.shares * pos.entry_price
        realized = net - cost
        return_pct = (price - pos.entry_price) / pos.entry_price

        self.realized_pnl += realized
        self.cash += net
        self.pending_settlements.append(
            Settlement(next_business_day(today), net)
        )

        iso_cal = _to_date(pos.entry_date).isocalendar()
        week_id = f"{iso_cal[0]}-W{iso_cal[1]:02d}"

        result = WeeklyResult(
            symbol=pos.symbol,
            week_id=week_id,
            entry_date=pos.entry_date,
            entry_price=pos.entry_price,
            exit_date=today,
            exit_price=price,
            exit_reason=reason,
            return_pct=return_pct,
            pnl=realized,
            score=pos.score,
            convergence_count=pos.convergence_count,
            signals=pos.signals,
        )
        self.weekly_results.append(result)

        if reason == "hard_stop":
            cooldown_end = _to_date(today) + timedelta(weeks=STOP_COOLDOWN_WEEKS)
            self.cooldowns[pos.symbol] = cooldown_end.strftime("%Y-%m-%d")

        self.position = None
        self.trades_count += 1
        return realized

    def check_stop(self, current_price: float) -> bool:
        if self.position is None:
            return False
        return current_price <= self.position.stop_price

    def should_time_stop(self, today: str) -> bool:
        if self.position is None:
            return False
        return today >= self.position.exit_date

    def liquidate(self, marks: dict[str, float], today: str) -> Optional[float]:
        if self.position is None:
            return None
        px = marks.get(self.position.symbol, self.position.entry_price)
        was_halted = self.halted
        self.halted = False
        try:
            return self.exit(price=px, today=today, reason="liquidation")
        finally:
            self.halted = was_halted

    # ------- calibration -------

    def hit_rate(self) -> Optional[float]:
        if not self.weekly_results:
            return None
        hits = sum(1 for r in self.weekly_results if r.return_pct > 0)
        return hits / len(self.weekly_results)

    def graded_count(self) -> int:
        return len(self.weekly_results)

    def avg_return(self) -> Optional[float]:
        if not self.weekly_results:
            return None
        return sum(r.return_pct for r in self.weekly_results) / len(self.weekly_results)

    def convergence_hit_rates(self) -> dict[int, Optional[float]]:
        by_count: dict[int, list[float]] = {}
        for r in self.weekly_results:
            by_count.setdefault(r.convergence_count, []).append(
                1.0 if r.return_pct > 0 else 0.0
            )
        return {
            k: sum(v) / len(v) if v else None
            for k, v in sorted(by_count.items())
        }

    def signal_attribution(self) -> dict[str, dict]:
        by_signal: dict[str, list[float]] = {}
        for r in self.weekly_results:
            for sig, active in r.signals.items():
                if active:
                    by_signal.setdefault(sig, []).append(r.return_pct)
        out = {}
        for sig, returns in by_signal.items():
            n = len(returns)
            hits = sum(1 for r in returns if r > 0)
            out[sig] = {
                "n": n,
                "hit_rate": hits / n if n else 0,
                "avg_return": sum(returns) / n if n else 0,
            }
        return out

    # ------- persistence -------

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "cash": self.cash,
            "position": asdict(self.position) if self.position else None,
            "peak_equity": self.peak_equity,
            "realized_pnl": self.realized_pnl,
            "trades_count": self.trades_count,
            "halted": self.halted,
            "contributed_cash": self.contributed_cash,
            "pending_settlements": [asdict(s) for s in self.pending_settlements],
            "gfv_count": self.gfv_count,
            "cooldowns": dict(self.cooldowns),
            "weekly_results": [asdict(r) for r in self.weekly_results],
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "MidasSleeve":
        s = cls(initial_cash=0.0)
        s.cash = float(data["cash"])
        pos = data.get("position")
        s.position = MidasPosition(**pos) if pos else None
        s.peak_equity = float(data.get("peak_equity", s.cash))
        s.realized_pnl = float(data.get("realized_pnl", 0.0))
        s.trades_count = int(data.get("trades_count", 0))
        s.halted = bool(data.get("halted", False))
        s.contributed_cash = float(data.get("contributed_cash", s.cash))
        s.pending_settlements = [
            Settlement(**x) for x in data.get("pending_settlements", [])
        ]
        s.gfv_count = int(data.get("gfv_count", 0))
        s.cooldowns = dict(data.get("cooldowns", {}))
        s.weekly_results = [
            WeeklyResult(**r) for r in data.get("weekly_results", [])
        ]
        return s

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: str) -> "MidasSleeve":
        with open(path) as f:
            return cls.from_dict(json.load(f))
