#!/usr/bin/env python3
"""Quality-lens validation -- one-shot ghost open (backlog #2,
docs/lab_prereg_quality_lens_validation.md).

Measurement study (skips shared.lab's registry per the /lab liturgy's
own example). Freezes the 100-name 2026-06-28 quarterly-screen
population and its `lenses.quality` field verbatim, opens ONE ghost
entry per symbol at the first available market price after the prereg
commit date, and leaves grading (shared.ghost.numeric_tercile_stats on
the frozen `quality` feature) to a future /lab session once the 6mo/
12mo horizons elapse. NOT a rolling population -- run once.

NO broker orders, NO sleeve mutation.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import ghost

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("quality_lens_validation")

SCREEN_PATH = "cache/oracle_screen.json"
QUOTES_PATH = sys.argv[1] if len(sys.argv) > 1 else None
GHOST_LEDGER_PATH = "cache/lab_ghost_ledger.json"
SOURCE = "quality_lens_validation"

# The last regular-session trade available at prereg-commit time
# (2026-07-04 is itself a market holiday weekend -- July 3 observed,
# July 4/5 weekend; the last real session was 2026-07-02). Using an
# actual traded price 2 days OLDER than the commit date, not a future
# one -- the opposite of a look-ahead risk, and disclosed in the
# results doc as a practical execution note.
ENTRY_DATE = "2026-07-02"


def main():
    with open(SCREEN_PATH) as f:
        screen = json.load(f)
    with open(QUOTES_PATH) as f:
        quotes = json.load(f)

    existing = ghost.load_ledger(GHOST_LEDGER_PATH) if os.path.exists(GHOST_LEDGER_PATH) else []
    already = {e.symbol for e in existing if e.source == SOURCE}
    if already:
        log.warning("source %r already has %d entries -- this study is one-shot, "
                     "re-running would double the population; aborting", SOURCE, len(already))
        return

    opened = 0
    missing_price = []
    for row in screen["rows"]:
        sym = row["symbol"].upper()
        price = quotes.get(sym)
        if not price:
            missing_price.append(sym)
            continue
        quality = row["lenses"]["quality"]
        entry = ghost.GhostEntry(
            symbol=sym, entry_date=ENTRY_DATE, entry_price=float(price),
            horizon_days=365, source=SOURCE,
            features={
                "strategy": SOURCE, "quality": quality,
                "insider_tier": row.get("insider_tier"),
                "market_cap": row.get("market_cap"),
                "screen_date": "2026-06-28",
            },
        )
        existing.append(entry)
        opened += 1

    ghost.save_ledger(GHOST_LEDGER_PATH, existing)
    log.info("opened %d/%d entries (ledger now %d total across all sources)",
              opened, len(screen["rows"]), len(existing))
    if missing_price:
        log.warning("no quote for %d symbols: %s", len(missing_price), missing_price)


if __name__ == "__main__":
    main()
