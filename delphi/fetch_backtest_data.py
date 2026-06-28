#!/usr/bin/env python3
"""Fetch historical price + fundamental data for the Delphi backtest.

This is a standalone helper — the backtest itself reads from JSON cache files.
Run this once to populate the cache, then iterate on the backtest without
re-fetching.

In practice this is called by the /delphi skill or manually; it uses the
Robinhood MCP tools via the Claude harness, so it can't run as a plain
Python script. Instead, the skill invokes the fetch functions and writes
the results to cache/.

This module defines the symbols and output paths so the backtest and the
skill agree on what to fetch and where to store it.
"""
from __future__ import annotations

from delphi.backtest import ALL_ETFS, ALL_STOCK_SYMBOLS, SECTOR_CONSTITUENTS

SECTOR_PRICES_PATH = "cache/delphi_bt_sector_prices.json"
STOCK_PRICES_PATH = "cache/delphi_bt_stock_prices.json"
FUNDAMENTALS_PATH = "cache/delphi_bt_fundamentals.json"

# Re-export for the skill to import
SYMBOLS_TO_FETCH = {
    "etfs": ALL_ETFS,
    "stocks": ALL_STOCK_SYMBOLS,
    "sector_constituents": SECTOR_CONSTITUENTS,
}
