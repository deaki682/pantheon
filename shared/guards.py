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


# ------- Liquidate-on-kill helper -------

def liquidate_if_kill(sleeve, marks: dict[str, float], today: str):
    """If KILL_SWITCH exists, force-liquidate every position. Returns the list
    of (symbol, shares, price) that were sold, or None if no action was taken."""
    if not kill_switch_active():
        return None
    if hasattr(sleeve, "liquidate_all"):
        return sleeve.liquidate_all(marks, today)
    return None
