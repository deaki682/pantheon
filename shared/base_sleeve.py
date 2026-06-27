"""BaseSleeve — common book-keeping for Oracle and Delphi.

Achilles does NOT inherit from this — its event-keyed position model is
fundamentally different.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


FEE_BPS = 5  # 5 basis points per trade (modeled commission/slippage)


def _to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def next_business_day(today: str) -> str:
    """Return the next business day after `today` (skips Saturday and Sunday)."""
    d = _to_date(today)
    while True:
        d = d + timedelta(days=1)
        # Monday=0 ... Sunday=6
        if d.weekday() < 5:
            return _to_str(d)


def add_days(today: str, days: int) -> str:
    """Calendar-day add (does NOT skip weekends — for cooldown windows)."""
    d = _to_date(today)
    return _to_str(d + timedelta(days=days))


@dataclass
class SleevePosition:
    shares: float
    avg_price: float
    entry_date: str
    sector: str = ""


@dataclass
class Settlement:
    settle_date: str
    amount: float


class SleeveHalted(Exception):
    """Raised when an action is attempted on a halted sleeve. The buy()/sell()
    public API returns False instead of raising — this is reserved for code
    paths that want to be explicit."""


class BaseSleeve:
    """Common cash/position book-keeping.

    Subclasses set `cooldown_days` and may override defaults. Buys deduct a
    5bp fee, sells credit proceeds minus 5bp. Sells track T+1 settlement
    and a buy using unsettled cash flags a good-faith-violation count.
    """

    cooldown_days: int = 0

    def __init__(self, name: str, initial_cash: float = 1000.0):
        self.name = name
        self.cash: float = float(initial_cash)
        self.positions: dict[str, SleevePosition] = {}
        self.pending_settlements: list[Settlement] = []
        self.realized_pnl: float = 0.0
        self.gfv_count: int = 0
        self.trades_count: int = 0
        self.cooldowns: dict[str, str] = {}
        self.halted: bool = False
        self.contributed_cash: float = float(initial_cash)

    # ------- accounting -------

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

    def equity(self, marks: Optional[dict[str, float]] = None) -> float:
        """Total equity = cash + sum(shares * mark). Missing marks fall back
        to avg_price (treat as held flat)."""
        marks = marks or {}
        total = self.cash
        for sym, pos in self.positions.items():
            mark = marks.get(sym, pos.avg_price)
            total += pos.shares * mark
        return total

    def unsettled_cash(self, today: str) -> float:
        """Sum of pending settlements whose settle date is strictly after today."""
        return sum(s.amount for s in self.pending_settlements if s.settle_date > today)

    def settled_cash(self, today: str) -> float:
        return self.cash - self.unsettled_cash(today)

    def process_settlements(self, today: str) -> None:
        """Drop entries whose settle date is on or before today."""
        self.pending_settlements = [
            s for s in self.pending_settlements if s.settle_date > today
        ]

    # ------- trading -------

    def buy(
        self,
        symbol: str,
        shares: float,
        price: float,
        today: str,
        sector: str = "",
    ) -> bool:
        # halted check FIRST — load-bearing.
        if self.halted:
            return False
        if shares <= 0 or price <= 0:
            return False
        if symbol in self.cooldowns and self.cooldowns[symbol] > today:
            return False
        dollars = shares * price
        fee = dollars * FEE_BPS / 10_000
        total_cost = dollars + fee
        if total_cost > self.cash + 1e-9:
            return False
        # GFV tracking: buying with unsettled cash flags a potential violation
        if total_cost > self.settled_cash(today) + 1e-9:
            self.gfv_count += 1
        if symbol in self.positions:
            existing = self.positions[symbol]
            new_shares = existing.shares + shares
            new_avg = (existing.shares * existing.avg_price + dollars) / new_shares
            self.positions[symbol] = SleevePosition(
                shares=new_shares,
                avg_price=new_avg,
                entry_date=existing.entry_date,
                sector=existing.sector or sector,
            )
        else:
            self.positions[symbol] = SleevePosition(
                shares=shares, avg_price=price, entry_date=today, sector=sector
            )
        self.cash -= total_cost
        self.trades_count += 1
        return True

    def sell(
        self,
        symbol: str,
        shares: float,
        price: float,
        today: str,
        set_cooldown: bool = True,
    ) -> bool:
        if self.halted:
            # Halted blocks new buys; selling-to-flatten is OK from the rails
            # POV, but the public API requires explicit `force=True` via
            # liquidate_all(). Treat plain sell() as blocked when halted.
            return False
        if symbol not in self.positions:
            return False
        pos = self.positions[symbol]
        if shares <= 0 or shares > pos.shares + 1e-9:
            return False
        if price <= 0:
            return False
        dollars = shares * price
        fee = dollars * FEE_BPS / 10_000
        proceeds = dollars - fee
        realized = (price - pos.avg_price) * shares - fee
        self.realized_pnl += realized
        self.cash += proceeds
        self.pending_settlements.append(
            Settlement(settle_date=next_business_day(today), amount=proceeds)
        )
        pos.shares -= shares
        if pos.shares <= 1e-9:
            del self.positions[symbol]
        if set_cooldown and self.cooldown_days > 0:
            self.cooldowns[symbol] = add_days(today, self.cooldown_days)
        self.trades_count += 1
        return True

    def liquidate_all(self, marks: dict[str, float], today: str) -> list[tuple[str, float, float]]:
        """Force-sell every position at the supplied marks. Used by the kill
        switch — bypasses the halted guard."""
        sold: list[tuple[str, float, float]] = []
        was_halted = self.halted
        self.halted = False
        try:
            for sym in list(self.positions.keys()):
                pos = self.positions[sym]
                shares_before = pos.shares
                px = marks.get(sym, pos.avg_price)
                if self.sell(sym, shares_before, px, today, set_cooldown=False):
                    sold.append((sym, shares_before, px))
        finally:
            self.halted = was_halted
        return sold

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
            "cooldowns": dict(self.cooldowns),
            "halted": self.halted,
            "contributed_cash": self.contributed_cash,
            "cooldown_days": self.cooldown_days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BaseSleeve":
        s = cls(data.get("name", cls.__name__), initial_cash=0.0)
        s.cash = float(data["cash"])
        s.positions = {
            k: SleevePosition(**v) for k, v in data.get("positions", {}).items()
        }
        s.pending_settlements = [
            Settlement(**x) for x in data.get("pending_settlements", [])
        ]
        s.realized_pnl = float(data.get("realized_pnl", 0.0))
        s.gfv_count = int(data.get("gfv_count", 0))
        s.trades_count = int(data.get("trades_count", 0))
        s.cooldowns = dict(data.get("cooldowns", {}))
        s.halted = bool(data.get("halted", False))
        s.contributed_cash = float(data.get("contributed_cash", s.cash))
        return s

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: str) -> "BaseSleeve":
        with open(path) as f:
            return cls.from_dict(json.load(f))
