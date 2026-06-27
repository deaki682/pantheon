"""DelphiSleeve — sector momentum rotator.

- Cooldown after sells: 7 days (faster rotation than Oracle).
- Minimum trade: $25 (smaller sleeve).
- Per-name cap: 12%. Per-sector cap: 40%. Up to 4 names per sector.
- Cash floor: 10%. Rebalance band: 20%.
- ETF blocklist: never trade the sector ETFs or SPY themselves.
"""
from __future__ import annotations

from shared.base_sleeve import BaseSleeve


COOLDOWN_DAYS = 7
MIN_TICKET = 25.0
PER_NAME_CAP = 0.12
PER_SECTOR_CAP = 0.40
MAX_NAMES_PER_SECTOR = 4
CASH_FLOOR = 0.10
REBAL_BAND = 0.20

# Never buy these — Delphi picks individual stocks INSIDE sectors, not the
# sector ETFs themselves.
SECTOR_ETFS = ("XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE", "XLB", "XLC")
BLOCKLIST = set(SECTOR_ETFS) | {"SPY", "VOO", "IVV", "QQQ", "DIA", "IWM"}


def is_blocked(symbol: str) -> bool:
    return symbol.upper() in BLOCKLIST


class DelphiSleeve(BaseSleeve):
    cooldown_days = COOLDOWN_DAYS

    def __init__(self, name: str = "delphi", initial_cash: float = 1_000.0):
        super().__init__(name=name, initial_cash=initial_cash)

    def buy(self, symbol, shares, price, today, sector=""):
        if is_blocked(symbol):
            return False
        return super().buy(symbol, shares, price, today, sector)
