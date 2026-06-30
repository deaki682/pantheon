"""DelphiSleeve — momentum compounder.

- Cooldown after sells: 7 days.
- Minimum trade: $25.
- Per-name cap: 20%. Cash floor: 5%. Rebalance band: 20%.
- Holds top 10 by 13-week momentum, exits on 4-week MA break.
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


class DelphiSleeve(BaseSleeve):
    cooldown_days = COOLDOWN_DAYS

    def __init__(self, name: str = "delphi", initial_cash: float = 1_000.0):
        super().__init__(name=name, initial_cash=initial_cash)
