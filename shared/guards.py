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


# ------- Cross-god position sanity check -------

import logging as _logging

_guard_log = _logging.getLogger("shared.guards")

SLEEVE_PATHS = {
    "oracle": "cache/oracle_sleeve.json",
    "delphi": "cache/delphi_sleeve.json",
    "achilles": "cache/achilles_sleeve.json",
}


def _load_sleeve_shares(path: str) -> dict[str, float]:
    """Load a sleeve JSON and return {SYMBOL: total_shares}.

    Works for both BaseSleeve-style (positions keyed by symbol) and
    AchillesSleeve-style (positions keyed by event_id with a symbol field).
    Returns empty dict if the file doesn't exist or can't be parsed.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    positions = data.get("positions", {})
    out: dict[str, float] = {}
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


def check_position_sanity(
    broker_positions: dict[str, float],
    *,
    sleeve_paths: Optional[dict[str, str]] = None,
    tolerance: float = 0.01,
) -> list[PositionMismatch]:
    """Compare broker's per-symbol share count against the sum of all sleeves.

    `broker_positions` is {SYMBOL: shares} from the broker's actual holdings.
    Returns a list of mismatches where the difference exceeds `tolerance` shares.

    Call this before placing orders to catch sleeve drift early.
    """
    combined = aggregate_sleeve_shares(sleeve_paths)
    mismatches: list[PositionMismatch] = []

    # Only check positions that at least one sleeve claims. Broker-only
    # positions (pre-existing, manually placed) are invisible to the gods.
    for sym in sorted(combined.keys()):
        broker_shares = broker_positions.get(sym, 0.0)
        per_god = combined[sym]
        sleeve_total = sum(per_god.values())
        if abs(sleeve_total - broker_shares) > tolerance:
            mismatches.append(PositionMismatch(
                symbol=sym,
                sleeve_total=sleeve_total,
                broker_shares=broker_shares,
                per_god=dict(per_god),
            ))
            _guard_log.warning(
                "POSITION MISMATCH %s: sleeves=%.4f shares, broker=%.4f shares, "
                "per_god=%s",
                sym, sleeve_total, broker_shares, per_god,
            )

    return mismatches


def pre_trade_check(
    broker_positions: dict[str, float],
    *,
    sleeve_paths: Optional[dict[str, str]] = None,
    tolerance: float = 0.01,
) -> bool:
    """Return True if all sleeve positions match the broker. Log and return
    False if any mismatch is found — the caller should halt trading until
    reconciliation resolves the drift."""
    mismatches = check_position_sanity(
        broker_positions, sleeve_paths=sleeve_paths, tolerance=tolerance,
    )
    if mismatches:
        _guard_log.error(
            "PRE-TRADE CHECK FAILED: %d symbol(s) out of sync with broker. "
            "Run /oracle-reconcile before trading.",
            len(mismatches),
        )
        return False
    return True


# ------- Liquidate-on-kill helper -------

def liquidate_if_kill(sleeve, marks: dict[str, float], today: str):
    """If KILL_SWITCH exists, force-liquidate every position. Returns the list
    of (symbol, shares, price) that were sold, or None if no action was taken."""
    if not kill_switch_active():
        return None
    if hasattr(sleeve, "liquidate_all"):
        return sleeve.liquidate_all(marks, today)
    return None
