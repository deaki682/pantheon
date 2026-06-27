"""OracleSleeve — patient, long-horizon book.

- Hard cap: $12,000 total capital allocation (CEILING).
- Hard floor on starting capital: $1,000 (BASE).
- Cooldown after sells: 31 days (wash-sale aligned).
- Minimum trade size: $50.
- Per-name cap: 15%. Per-sector cap: 35%. Cash floor: 10%.
"""
from __future__ import annotations

from shared.base_sleeve import BaseSleeve


CAPITAL_CEILING = 12_000.0
CAPITAL_BASE = 1_000.0
ACHILLES_RESERVE = 1_000.0  # reserved out of the ceiling for Achilles
COOLDOWN_DAYS = 31
MIN_TICKET = 50.0
PER_NAME_CAP = 0.25  # let a top-conviction idea reach ~25% so it actually moves the book
PER_SECTOR_CAP = 0.35
CASH_FLOOR = 0.10
MAX_POSITIONS = 8  # concentration target: a $1k research book holds the best ~5–8 names

# Circuit breakers
DERISK_DRAWDOWN_VS_MARKET = 0.15  # 15% excess drawdown vs market -> derisk
HALT_ABSOLUTE_DRAWDOWN = 0.32  # 32% absolute drawdown -> halt


class OracleSleeve(BaseSleeve):
    cooldown_days = COOLDOWN_DAYS

    def __init__(self, name: str = "oracle", initial_cash: float = CAPITAL_BASE):
        super().__init__(name=name, initial_cash=initial_cash)
        # Track peak equity for drawdown computation.
        self.peak_equity: float = initial_cash

    def update_peak(self, marks: dict[str, float] | None = None) -> None:
        eq = self.equity(marks or {})
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: dict[str, float] | None = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        eq = self.equity(marks or {})
        return max(0.0, 1.0 - eq / self.peak_equity)

    def excess_drawdown_vs_market(
        self, marks: dict[str, float] | None, market_drawdown: float
    ) -> float:
        return max(0.0, self.absolute_drawdown(marks) - market_drawdown)

    def check_circuit_breakers(
        self, marks: dict[str, float] | None, market_drawdown: float = 0.0
    ) -> str:
        """Return one of 'ok' | 'derisk' | 'halt'."""
        # Use a small epsilon to avoid floating-point boundary surprises.
        if self.absolute_drawdown(marks) >= HALT_ABSOLUTE_DRAWDOWN - 1e-9:
            self.halted = True
            return "halt"
        if self.excess_drawdown_vs_market(marks, market_drawdown) >= DERISK_DRAWDOWN_VS_MARKET - 1e-9:
            return "derisk"
        return "ok"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["peak_equity"] = self.peak_equity
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "OracleSleeve":
        s = super().from_dict(data)
        s.__class__ = cls  # type: ignore[assignment]
        s.peak_equity = float(data.get("peak_equity", s.cash))  # type: ignore[attr-defined]
        return s  # type: ignore[return-value]
