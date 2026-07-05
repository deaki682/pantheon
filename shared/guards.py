"""Safety rails shared across all three gods.

- Kill switch: a file named `KILL_SWITCH` in the cwd triggers full liquidation.
- Live-trading gate: only enabled when the per-god env var is exactly "true".
- Order ledger: per-god JSONL of every order this god placed. Used to filter
  the broker's order list to just this god's orders — preventing cross-bot
  confusion when three gods share one account.
- Placement guards: same-day duplicate-order prevention per god.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, date
from typing import Iterable, Optional


KILL_SWITCH_FILE = "KILL_SWITCH"


def kill_switch_active(cwd: Optional[str] = None) -> bool:
    """Returns True iff a file named KILL_SWITCH exists at the given cwd
    (default: actual process cwd). No override — if the file is there, the
    gods liquidate. Period."""
    base = cwd if cwd is not None else "."
    return os.path.exists(os.path.join(base, KILL_SWITCH_FILE))


_LIVE_ENV = {
    "oracle": "ORACLE_LIVE",
    "delphi": "DELPHI_LIVE",
    "achilles": "ACHILLES_LIVE",
    "midas": "MIDAS_LIVE",
    "nemesis": "NEMESIS_LIVE",
    "proteus": "PROTEUS_LIVE",
    "plutus": "PLUTUS_LIVE",
    "hermes": "HERMES_LIVE",
}


def is_live(god: str, env: Optional[dict] = None) -> bool:
    """True only if the matching env var is exactly the string 'true'."""
    env = env if env is not None else os.environ
    var = _LIVE_ENV.get(god.lower())
    if not var:
        return False
    return env.get(var, "").strip().lower() == "true"


# ------- Order ledger -------

@dataclass
class OrderRecord:
    order_id: str
    symbol: str
    side: str  # "buy" | "sell"
    dollars: float
    date: str  # YYYY-MM-DD


def append_order(path: str, record: OrderRecord) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record.__dict__, sort_keys=True) + "\n")


def read_ledger(path: str) -> list[OrderRecord]:
    if not os.path.exists(path):
        return []
    out: list[OrderRecord] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(OrderRecord(**d))
            except Exception:
                continue
    return out


def filter_orders_by_ledger(
    broker_orders: Iterable[dict],
    ledger: Iterable[OrderRecord],
    id_field: str = "order_id",
) -> list[dict]:
    """Return only the broker orders whose IDs appear in this god's ledger.

    SAFETY: if the ledger is empty, this returns an EMPTY LIST. Never return
    all broker orders as 'ours' — that would let one god grab another god's
    fills.
    """
    our_ids: set[str] = {r.order_id for r in ledger}
    if not our_ids:
        return []
    return [o for o in broker_orders if str(o.get(id_field)) in our_ids]


# ------- Same-day placement guard -------

def already_placed_today(
    ledger: Iterable[OrderRecord], symbol: str, side: str, today: str
) -> bool:
    """True if there's a ledger entry for this symbol+side on `today`."""
    for r in ledger:
        if r.symbol == symbol and r.side == side and r.date == today:
            return True
    return False


# ------- Broker position filter -------

LEDGER_PATHS = {
    "oracle": "cache/oracle_ledger.jsonl",
    "delphi": "cache/delphi_ledger.jsonl",
    "achilles": "cache/achilles_ledger.jsonl",
    "midas": "cache/midas_ledger.jsonl",
    "proteus": "cache/proteus_ledger.jsonl",
    "plutus": "cache/plutus_ledger.jsonl",
    "hermes": "cache/hermes_ledger.jsonl",
}


def _god_claimed_symbols(
    sleeve_paths: Optional[dict[str, str]] = None,
    ledger_paths: Optional[dict[str, str]] = None,
) -> set[str]:
    """Symbols that any god currently holds or has ever traded."""
    paths = sleeve_paths or SLEEVE_PATHS
    ledgers = ledger_paths or LEDGER_PATHS
    syms: set[str] = set()
    for path in paths.values():
        syms.update(_load_sleeve_shares(path).keys())
    for path in ledgers.values():
        for rec in read_ledger(path):
            syms.add(rec.symbol.upper())
    return syms


def filter_broker_to_gods(
    broker_positions: dict[str, float],
    *,
    sleeve_paths: Optional[dict[str, str]] = None,
    ledger_paths: Optional[dict[str, str]] = None,
) -> dict[str, float]:
    """Strip broker positions down to only symbols any god has claimed.

    The broker account holds pre-existing personal positions that the gods
    did not place. This filter makes them invisible so no god reasons about
    them, reconciles them, or mistakes them for its own.

    A symbol is "claimed" if it appears in any sleeve's positions OR in any
    god's order ledger. If no god has claimed anything, returns empty.
    """
    claimed = _god_claimed_symbols(sleeve_paths, ledger_paths)
    if not claimed:
        return {}
    return {sym: shares for sym, shares in broker_positions.items() if sym.upper() in claimed}


# ------- Cross-god position sanity check -------

import logging as _logging

_guard_log = _logging.getLogger("shared.guards")

SLEEVE_PATHS = {
    "oracle": "cache/oracle_sleeve.json",
    "delphi": "cache/delphi_sleeve.json",
    "achilles": "cache/achilles_sleeve.json",
    "nemesis": "cache/nemesis_sleeve.json",
    "midas": "cache/midas_sleeve.json",
    "proteus": "cache/proteus_sleeve.json",
    "plutus": "cache/plutus_sleeve.json",
    "hermes": "cache/hermes_sleeve.json",
}


def _load_sleeve_shares(path: str) -> dict[str, float]:
    """Load a sleeve JSON and return {SYMBOL: total_shares}.

    Works for BaseSleeve-style (positions keyed by symbol),
    AchillesSleeve-style (positions keyed by event_id with a symbol field),
    and MidasSleeve-style (single "position" field, dict or None).
    Returns empty dict if the file doesn't exist or can't be parsed.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, float] = {}
    # Midas: single "position" field
    single = data.get("position")
    if isinstance(single, dict) and single.get("symbol"):
        sym = single["symbol"].upper()
        out[sym] = float(single.get("shares", 0))
        return out
    # Oracle/Delphi/Achilles: "positions" dict
    positions = data.get("positions", {})
    for key, pos in positions.items():
        if not isinstance(pos, dict):
            continue
        sym = pos.get("symbol", key).upper()
        shares = float(pos.get("shares", 0))
        out[sym] = out.get(sym, 0.0) + shares
    return out


def aggregate_sleeve_shares(
    sleeve_paths: Optional[dict[str, str]] = None,
) -> dict[str, dict[str, float]]:
    """Load all three sleeves and return {SYMBOL: {god: shares}}.

    Only includes symbols with non-zero shares.
    """
    paths = sleeve_paths or SLEEVE_PATHS
    per_god: dict[str, dict[str, float]] = {}
    for god, path in paths.items():
        per_god[god] = _load_sleeve_shares(path)

    combined: dict[str, dict[str, float]] = {}
    for god, shares_map in per_god.items():
        for sym, shares in shares_map.items():
            if shares > 1e-9:
                combined.setdefault(sym, {})[god] = shares
    return combined


@dataclass
class PositionMismatch:
    symbol: str
    sleeve_total: float
    broker_shares: float
    per_god: dict[str, float]


PENDING_ORDER_STATES = frozenset({"queued", "confirmed", "unconfirmed", "partially_filled"})


def pending_shares_from_orders(
    broker_orders: list[dict],
) -> dict[str, float]:
    """Extract {SYMBOL: unfilled_shares} from broker orders in pending states.

    Pending states: queued, confirmed, unconfirmed, partially_filled.
    For each, unfilled = quantity - cumulative_quantity.
    """
    pending: dict[str, float] = {}
    for order in broker_orders:
        state = (order.get("state") or "").lower()
        if state not in PENDING_ORDER_STATES:
            continue
        sym = (order.get("symbol") or "").upper()
        if not sym:
            continue
        qty = float(order.get("quantity") or 0)
        filled = float(order.get("cumulative_quantity") or 0)
        unfilled = qty - filled
        if unfilled > 0:
            side = (order.get("side") or "").lower()
            if side == "buy":
                pending[sym] = pending.get(sym, 0.0) + unfilled
            elif side == "sell":
                pending[sym] = pending.get(sym, 0.0) - unfilled
    return pending


def check_position_sanity(
    broker_positions: dict[str, float],
    *,
    sleeve_paths: Optional[dict[str, str]] = None,
    pending_orders: Optional[dict[str, float]] = None,
    tolerance: float = 0.01,
) -> list[PositionMismatch]:
    """Compare broker's per-symbol share count against the sum of all sleeves.

    `broker_positions` is {SYMBOL: shares} from the broker's actual holdings.
    `pending_orders` is {SYMBOL: unfilled_shares} from queued/confirmed orders
    that haven't filled yet (from `pending_shares_from_orders`). When provided,
    unfilled buy shares are added to broker_shares before comparing, so queued
    orders don't trigger false mismatches.

    Returns a list of mismatches where the difference exceeds `tolerance` shares.
    Call this before placing orders to catch sleeve drift early.
    """
    combined = aggregate_sleeve_shares(sleeve_paths)
    pending = pending_orders or {}
    mismatches: list[PositionMismatch] = []

    # Only check positions that at least one sleeve claims. Broker-only
    # positions (pre-existing, manually placed) are invisible to the gods.
    # One-sided check: only flag when the sleeve claims MORE than the broker
    # holds. The broker having extra shares is expected when the user's
    # personal holdings overlap with a god's symbols.
    for sym in sorted(combined.keys()):
        broker_shares = broker_positions.get(sym, 0.0)
        broker_plus_pending = broker_shares + pending.get(sym, 0.0)
        per_god = combined[sym]
        sleeve_total = sum(per_god.values())
        if sleeve_total - broker_plus_pending > tolerance:
            mismatches.append(PositionMismatch(
                symbol=sym,
                sleeve_total=sleeve_total,
                broker_shares=broker_shares,
                per_god=dict(per_god),
            ))
            _guard_log.warning(
                "POSITION MISMATCH %s: sleeves=%.4f shares, broker=%.4f shares "
                "(+%.4f pending), per_god=%s",
                sym, sleeve_total, broker_shares, pending.get(sym, 0.0), per_god,
            )

    return mismatches


def pre_trade_check(
    broker_positions: dict[str, float],
    *,
    sleeve_paths: Optional[dict[str, str]] = None,
    pending_orders: Optional[dict[str, float]] = None,
    tolerance: float = 0.01,
) -> bool:
    """Return True if all sleeve positions match the broker. Log and return
    False if any mismatch is found — the caller should halt trading until
    reconciliation resolves the drift.

    Pass `pending_orders` (from `pending_shares_from_orders`) to account for
    queued/confirmed orders that haven't filled yet — e.g. orders placed on
    a weekend waiting for Monday open.
    """
    mismatches = check_position_sanity(
        broker_positions, sleeve_paths=sleeve_paths,
        pending_orders=pending_orders, tolerance=tolerance,
    )
    if mismatches:
        _guard_log.error(
            "PRE-TRADE CHECK FAILED: %d symbol(s) out of sync with broker. "
            "Run /oracle-reconcile before trading.",
            len(mismatches),
        )
        return False
    return True


# ------- Secondary-price staleness guard -------

def secondary_price_suspect(
    secondary_price: float, broker_price: float, tolerance: float = 0.15
) -> bool:
    """True when a price from a NON-broker source (web search, news article,
    cached screen) disagrees with the broker's tape by more than `tolerance`.

    Added 2026-07-04 (Proteus self-review finding #6) after a web-reported
    $32 print turned out to be five months stale against the broker's real
    $19 tape. The broker quote is the reference; a flagged secondary price
    must not be used for any sizing, thesis math, or journal record.
    Non-positive or missing inputs are suspect by definition.
    """
    try:
        s, b = float(secondary_price), float(broker_price)
    except (TypeError, ValueError):
        return True
    if s <= 0 or b <= 0:
        return True
    return abs(s - b) / b > tolerance


# ------- Liquidate-on-kill helper -------

def liquidate_if_kill(sleeve, marks: dict[str, float], today: str):
    """If KILL_SWITCH exists, force-liquidate every position. Returns the list
    of (symbol, shares, price) that were sold, or None if no action was taken."""
    if not kill_switch_active():
        return None
    if hasattr(sleeve, "liquidate_all"):
        return sleeve.liquidate_all(marks, today)
    return None
