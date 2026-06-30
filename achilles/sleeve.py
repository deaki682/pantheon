"""AchillesSleeve — single-position PEAD sleeve.

One position at a time. Enter on earnings beat, exit after 5 trading
days or on -8% stop. Standalone (does NOT inherit BaseSleeve).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Optional


CAPITAL_BASE = 1_000.0
HARD_STOP_PCT = -0.08
HALT_DRAWDOWN = 0.40
FEE_BPS = 5
HOLD_DAYS = 5
STOP_COOLDOWN_WEEKS = 4


def _to_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def next_business_day(today: str) -> str:
    d = _to_date(today)
    while True:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            return d.strftime("%Y-%m-%d")


def trading_days_ahead(today: str, n: int) -> str:
    d = _to_date(today)
    count = 0
    while count < n:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            count += 1
    return d.strftime("%Y-%m-%d")


@dataclass
class AchillesPosition:
    symbol: str
    shares: float
    entry_price: float
    entry_date: str
    stop_price: float
    exit_date: str
    score: float
    surprise_pct: float
    revenue_beat: bool = False
    guidance_raised: bool = False
    short_float_pct: Optional[float] = None


@dataclass
class TradeResult:
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    exit_reason: str
    return_pct: float
    pnl: float
    score: float
    surprise_pct: float
    revenue_beat: bool = False
    guidance_raised: bool = False
    short_float_pct: Optional[float] = None


@dataclass
class Settlement:
    settle_date: str
    amount: float


class AchillesSleeve:

    def __init__(self, initial_cash: float = CAPITAL_BASE):
        self.name = "achilles"
        self.cash: float = float(initial_cash)
        self.position: Optional[AchillesPosition] = None
        self.peak_equity: float = float(initial_cash)
        self.realized_pnl: float = 0.0
        self.trades_count: int = 0
        self.halted: bool = False
        self.contributed_cash: float = float(initial_cash)
        self.pending_settlements: list[Settlement] = []
        self.gfv_count: int = 0
        self.cooldowns: dict[str, str] = {}
        self.trade_results: list[TradeResult] = []

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
        surprise_pct: float,
        revenue_beat: bool = False,
        guidance_raised: bool = False,
        short_float_pct: Optional[float] = None,
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
        exit_date = trading_days_ahead(today, HOLD_DAYS)

        self.position = AchillesPosition(
            symbol=symbol.upper(),
            shares=shares,
            entry_price=price,
            entry_date=today,
            stop_price=stop_price,
            exit_date=exit_date,
            score=score,
            surprise_pct=surprise_pct,
            revenue_beat=revenue_beat,
            guidance_raised=guidance_raised,
            short_float_pct=short_float_pct,
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

        result = TradeResult(
            symbol=pos.symbol,
            entry_date=pos.entry_date,
            entry_price=pos.entry_price,
            exit_date=today,
            exit_price=price,
            exit_reason=reason,
            return_pct=return_pct,
            pnl=realized,
            score=pos.score,
            surprise_pct=pos.surprise_pct,
            revenue_beat=pos.revenue_beat,
            guidance_raised=pos.guidance_raised,
            short_float_pct=pos.short_float_pct,
        )
        self.trade_results.append(result)

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
        if not self.trade_results:
            return None
        hits = sum(1 for r in self.trade_results if r.return_pct > 0)
        return hits / len(self.trade_results)

    def graded_count(self) -> int:
        return len(self.trade_results)

    def avg_return(self) -> Optional[float]:
        if not self.trade_results:
            return None
        return sum(r.return_pct for r in self.trade_results) / len(self.trade_results)

    def hit_rate_by_surprise_bucket(self) -> dict[str, Optional[float]]:
        buckets: dict[str, list[float]] = {
            "3-10%": [], "10-20%": [], "20-50%": [], "50%+": [],
        }
        for r in self.trade_results:
            pct = abs(r.surprise_pct)
            if pct < 10:
                buckets["3-10%"].append(1.0 if r.return_pct > 0 else 0.0)
            elif pct < 20:
                buckets["10-20%"].append(1.0 if r.return_pct > 0 else 0.0)
            elif pct < 50:
                buckets["20-50%"].append(1.0 if r.return_pct > 0 else 0.0)
            else:
                buckets["50%+"].append(1.0 if r.return_pct > 0 else 0.0)
        return {
            k: sum(v) / len(v) if v else None
            for k, v in buckets.items()
        }

    def confirming_signal_stats(self) -> dict[str, dict]:
        signals = {
            "revenue_beat": {"with": [], "without": []},
            "guidance_raised": {"with": [], "without": []},
            "short_squeeze": {"with": [], "without": []},
        }
        for r in self.trade_results:
            hit = 1.0 if r.return_pct > 0 else 0.0
            key = "with" if r.revenue_beat else "without"
            signals["revenue_beat"][key].append(hit)
            key = "with" if r.guidance_raised else "without"
            signals["guidance_raised"][key].append(hit)
            key = "with" if r.short_float_pct and r.short_float_pct > 20 else "without"
            signals["short_squeeze"][key].append(hit)
        out = {}
        for sig, groups in signals.items():
            out[sig] = {
                "with_hit_rate": sum(groups["with"]) / len(groups["with"]) if groups["with"] else None,
                "without_hit_rate": sum(groups["without"]) / len(groups["without"]) if groups["without"] else None,
                "with_n": len(groups["with"]),
                "without_n": len(groups["without"]),
            }
        return out

    # ------- persistence -------

    def to_dict(self) -> dict:
        return {
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
            "trade_results": [asdict(r) for r in self.trade_results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AchillesSleeve":
        s = cls(initial_cash=0.0)
        s.cash = float(data["cash"])
        pos = data.get("position")
        s.position = AchillesPosition(**pos) if pos else None
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
        s.trade_results = [
            TradeResult(**r) for r in data.get("trade_results", [])
        ]
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
