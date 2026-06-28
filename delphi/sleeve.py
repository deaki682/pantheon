"""DelphiSleeve — sector momentum rotator.

- Cooldown after sells: 7 days (faster rotation than Oracle).
- Minimum trade: $25 (smaller sleeve).
- Per-name cap: 20%. Per-sector cap: 40%. Up to 2 names per sector.
- Cash floor: 10%. Rebalance band: 20%.
- ETF blocklist: never trade the sector ETFs themselves.
  SPY is allowed for the idle-cash overlay (core-satellite).
"""
from __future__ import annotations

from shared.base_sleeve import BaseSleeve


COOLDOWN_DAYS = 7
MIN_TICKET = 25.0
PER_NAME_CAP = 0.20
PER_SECTOR_CAP = 0.40
MAX_NAMES_PER_SECTOR = 2
CASH_FLOOR = 0.10
REBAL_BAND = 0.20

# Never buy as sector picks — Delphi picks individual stocks INSIDE sectors.
# SPY is excluded from the pick blocklist because it serves as the idle-cash
# overlay (core-satellite): excess cash buys SPY to maintain market exposure.
SECTOR_ETFS = ("XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE", "XLB", "XLC")
PICK_BLOCKLIST = set(SECTOR_ETFS) | {"VOO", "IVV", "QQQ", "DIA", "IWM"}
OVERLAY_SYMBOL = "SPY"


def is_blocked(symbol: str) -> bool:
    """Block sector ETFs and broad-market dupes from stock picks.
    SPY is allowed — it's the overlay vehicle, not a sector pick."""
    return symbol.upper() in PICK_BLOCKLIST


class DelphiSleeve(BaseSleeve):
    cooldown_days = COOLDOWN_DAYS

    def __init__(self, name: str = "delphi", initial_cash: float = 1_000.0):
        super().__init__(name=name, initial_cash=initial_cash)

    def buy(self, symbol, shares, price, today, sector=""):
        if is_blocked(symbol):
            return False
        return super().buy(symbol, shares, price, today, sector)
