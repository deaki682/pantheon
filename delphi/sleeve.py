"""DelphiSleeve — momentum compounder.

- Cooldown after sells: 7 days.
- Minimum trade: $25.
- Per-name cap: 20%. Cash floor: 5%. Rebalance band: 20%.
- Holds top 10 by 13-week momentum, exits on 4-week MA break.
- Circuit breaker: 40% drawdown from peak equity halts new buys.
"""
from __future__ import annotations

from shared.base_sleeve import BaseSleeve


COOLDOWN_DAYS = 7
MIN_TICKET = 25.0
PER_NAME_CAP = 0.20
CASH_FLOOR = 0.05
REBAL_BAND = 0.20
MAX_POSITIONS = 10
MOMENTUM_LOOKBACK = 65
MA_PERIOD = 20
HALT_DRAWDOWN = 0.40   # 40% drawdown from peak equity trips the circuit breaker


class DelphiSleeve(BaseSleeve):
    cooldown_days = COOLDOWN_DAYS

    def __init__(self, name: str = "delphi", initial_cash: float = 1_000.0):
        super().__init__(name=name, initial_cash=initial_cash)
        self.peak_equity: float = float(initial_cash)

    # ------- circuit breaker -------
    #
    # Momentum is the strategy most exposed to a sharp correlated drawdown (a
    # momentum crash). Track the high-water mark and halt new buys if equity
    # falls 40% from it, matching the other three gods.

    def update_peak(self, marks=None) -> None:
        eq = self.equity(marks)
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks=None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks) / self.peak_equity)

    def check_halt(self, marks=None) -> bool:
        """Trip the breaker (set halted) if drawdown >= HALT_DRAWDOWN."""
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    # ------- persistence (extend base to carry peak_equity) -------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["peak_equity"] = self.peak_equity
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DelphiSleeve":
        s = super().from_dict(data)
        # `or s.cash` heals a legacy null/absent peak — it self-corrects upward
        # on the next update_peak, and can't false-trip (equity >= cash = peak).
        s.peak_equity = float(data.get("peak_equity") or s.cash)  # type: ignore[attr-defined]
        return s
