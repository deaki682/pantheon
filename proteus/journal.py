"""Proteus — the discretionary ghost's journal and paper book.

The strategy layer is deliberately unconstrained (that is the
experiment; see docs/proteus_prereg.md). The DISCIPLINE lives here:
an append-only, validated journal that refuses stubs, and a paper book
that models costs honestly. Nothing in this module expresses an
opinion about what to buy — it only makes every opinion auditable.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date as _date
from typing import Optional

JOURNAL_PATH = "cache/ghost_proteus_journal.jsonl"
BOOK_PATH = "cache/ghost_proteus_book.json"
CURVE_PATH = "cache/ghost_proteus_curve.json"
BELIEFS_PATH = "cache/ghost_proteus_beliefs.md"

CAPITAL_BASE = 10_000.0
FEE_BPS = 5                      # per side, Pantheon standard
SHORT_BORROW_ANNUAL = 0.05       # flat, disclosed approximation
MAX_SHORT_GROSS = 0.50           # aggregate short exposure <= 50% of equity

EDGE_CLASSES = (
    "value", "momentum", "quality", "event_catalyst", "forced_flow",
    "post_earnings", "insider", "activist", "special_situation",
    "short_thesis", "macro_theme", "microstructure", "sentiment",
    "novel",   # genuinely outside the taxonomy — must be argued in the thesis
)

# The journal refuses unarticulated decisions. Lengths are floors for
# stubs, not quality bars — the grading does the quality judgment.
_PROSE_FLOORS = {
    "thesis": 200,
    "falsifiable_prediction": 80,
    "exit_plan": 40,
    "kill_condition": 20,
}

ENTER_FIELDS = ("date", "action", "symbol", "side", "dollars", "price",
                "spy_price", "horizon_days", "confidence", "edge_class",
                "thesis", "falsifiable_prediction", "exit_plan", "kill_condition")
EXIT_FIELDS = ("date", "action", "symbol", "price", "spy_price", "exit_reason")
EXIT_REASONS = ("exit_plan", "kill_condition", "horizon_expiry", "discretionary")
NOTE_FIELDS = ("date", "action", "text")


class JournalError(ValueError):
    """A malformed decision must fail loudly, never write quietly."""


def _require(record: dict, fields: tuple) -> None:
    missing = [f for f in fields if f not in record]
    if missing:
        raise JournalError(f"decision missing fields {missing}")


def validate_decision(record: dict) -> dict:
    """Validate one journal record. Returns it untouched on success."""
    if not isinstance(record, dict):
        raise JournalError(f"decision must be a dict, got {type(record).__name__}")
    action = record.get("action")
    if action == "enter":
        _require(record, ENTER_FIELDS)
        if record["side"] not in ("long", "short"):
            raise JournalError(f"side must be long|short, got {record['side']!r}")
        if not (isinstance(record["dollars"], (int, float)) and record["dollars"] > 0):
            raise JournalError("dollars must be a positive number")
        for px_field in ("price", "spy_price"):
            if not (isinstance(record[px_field], (int, float)) and record[px_field] > 0):
                raise JournalError(f"{px_field} must be a positive number")
        h = record["horizon_days"]
        if not (isinstance(h, int) and not isinstance(h, bool) and 1 <= h <= 365):
            raise JournalError(f"horizon_days must be int 1..365, got {h!r}")
        c = record["confidence"]
        if not (isinstance(c, (int, float)) and 0.0 <= c <= 1.0):
            raise JournalError(f"confidence must be in [0,1], got {c!r}")
        if record["edge_class"] not in EDGE_CLASSES:
            raise JournalError(
                f"edge_class {record['edge_class']!r} not in taxonomy {EDGE_CLASSES}")
        for name, floor in _PROSE_FLOORS.items():
            if len(str(record.get(name) or "")) < floor:
                raise JournalError(
                    f"{name} must be at least {floor} chars — "
                    f"an unarticulated decision is not a decision")
    elif action == "exit":
        _require(record, EXIT_FIELDS)
        if record["exit_reason"] not in EXIT_REASONS:
            raise JournalError(
                f"exit_reason {record['exit_reason']!r} not in {EXIT_REASONS}")
        for px_field in ("price", "spy_price"):
            if not (isinstance(record[px_field], (int, float)) and record[px_field] > 0):
                raise JournalError(f"{px_field} must be a positive number")
    elif action == "note":
        _require(record, NOTE_FIELDS)
        if len(str(record.get("text") or "")) < 40:
            raise JournalError("a note under 40 chars is not worth the line")
    else:
        raise JournalError(f"action must be enter|exit|note, got {action!r}")
    return record


def append_decision(record: dict, path: str = JOURNAL_PATH) -> None:
    """Validated, append-only write. There is no edit and no delete."""
    validate_decision(record)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def load_journal(path: str = JOURNAL_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


# ---------------------------------------------------------------- paper book

@dataclass
class Position:
    symbol: str
    side: str                # long | short
    dollars: float           # capital committed at entry
    shares: float
    entry_price: float
    entry_date: str
    spy_entry: float
    horizon_days: int
    confidence: float
    edge_class: str


@dataclass
class ClosedTrade:
    symbol: str
    side: str
    dollars: float
    entry_price: float
    exit_price: float
    entry_date: str
    exit_date: str
    exit_reason: str
    net_return: float        # after fees + borrow
    spy_return: float        # SPY over the identical window
    excess: float            # vs the passive mirror (long: SPY, short: -SPY)
    confidence: float
    edge_class: str
    horizon_days: int


@dataclass
class PaperBook:
    cash: float = CAPITAL_BASE
    positions: dict = field(default_factory=dict)    # symbol -> Position
    closed: list = field(default_factory=list)       # list[ClosedTrade]

    # -- persistence --
    @classmethod
    def load(cls, path: str = BOOK_PATH) -> "PaperBook":
        if not os.path.exists(path):
            return cls()
        raw = json.load(open(path))
        book = cls(cash=raw["cash"])
        book.positions = {s: Position(**p) for s, p in raw["positions"].items()}
        book.closed = [ClosedTrade(**t) for t in raw["closed"]]
        return book

    def save(self, path: str = BOOK_PATH) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        json.dump({
            "cash": self.cash,
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "closed": [asdict(t) for t in self.closed],
        }, open(path, "w"), indent=1)

    # -- exposure math --
    def short_gross(self) -> float:
        return sum(p.dollars for p in self.positions.values() if p.side == "short")

    def equity(self, marks: dict) -> float:
        """Cash + live value of longs + short P&L. marks: symbol -> price."""
        eq = self.cash
        for sym, p in self.positions.items():
            px = float(marks.get(sym, p.entry_price))
            if p.side == "long":
                eq += p.shares * px
            else:
                eq += p.dollars + p.shares * (p.entry_price - px)
        return eq

    # -- trades --
    def enter(self, *, symbol: str, side: str, dollars: float, price: float,
              date: str, spy_price: float, horizon_days: int,
              confidence: float, edge_class: str) -> Position:
        symbol = symbol.upper()
        if symbol in self.positions:
            raise JournalError(f"{symbol}: already open — one position per symbol")
        fee = dollars * FEE_BPS / 10_000
        if side == "long":
            if dollars + fee > self.cash + 1e-9:
                raise JournalError(
                    f"{symbol}: ${dollars:,.2f} exceeds cash ${self.cash:,.2f} — no leverage")
            self.cash -= dollars + fee
        elif side == "short":
            eq = self.equity({})
            if self.short_gross() + dollars > MAX_SHORT_GROSS * eq + 1e-9:
                raise JournalError(
                    f"{symbol}: short would take gross shorts past "
                    f"{MAX_SHORT_GROSS:.0%} of equity")
            # collateral is reserved from cash; returned at close with P&L
            if dollars + fee > self.cash + 1e-9:
                raise JournalError(
                    f"{symbol}: short collateral ${dollars:,.2f} exceeds cash")
            self.cash -= dollars + fee
        else:
            raise JournalError(f"side must be long|short, got {side!r}")
        pos = Position(symbol=symbol, side=side, dollars=dollars,
                       shares=dollars / price, entry_price=price,
                       entry_date=date, spy_entry=spy_price,
                       horizon_days=horizon_days, confidence=confidence,
                       edge_class=edge_class)
        self.positions[symbol] = pos
        return pos

    def exit(self, *, symbol: str, price: float, date: str,
             spy_price: float, exit_reason: str) -> ClosedTrade:
        symbol = symbol.upper()
        if symbol not in self.positions:
            raise JournalError(f"{symbol}: no open position to exit")
        p = self.positions.pop(symbol)
        held_days = max(1, (_date.fromisoformat(date) - _date.fromisoformat(p.entry_date)).days)
        if p.side == "long":
            proceeds = p.shares * price
            gross_ret = price / p.entry_price - 1
        else:
            pnl = p.shares * (p.entry_price - price)
            proceeds = p.dollars + pnl
            gross_ret = pnl / p.dollars
        fee = abs(proceeds) * FEE_BPS / 10_000
        borrow = (p.dollars * SHORT_BORROW_ANNUAL * held_days / 365
                  if p.side == "short" else 0.0)
        self.cash += proceeds - fee - borrow
        net_return = gross_ret - (fee + borrow) / p.dollars - FEE_BPS / 10_000
        spy_ret = spy_price / p.spy_entry - 1
        mirror = spy_ret if p.side == "long" else -spy_ret
        trade = ClosedTrade(
            symbol=symbol, side=p.side, dollars=p.dollars,
            entry_price=p.entry_price, exit_price=price,
            entry_date=p.entry_date, exit_date=date, exit_reason=exit_reason,
            net_return=round(net_return, 6), spy_return=round(spy_ret, 6),
            excess=round(net_return - mirror, 6),
            confidence=p.confidence, edge_class=p.edge_class,
            horizon_days=p.horizon_days,
        )
        self.closed.append(trade)
        return trade

    def horizon_expired(self, today: str) -> list[str]:
        """Symbols whose declared horizon has elapsed — must exit this session."""
        out = []
        for sym, p in self.positions.items():
            held = (_date.fromisoformat(today) - _date.fromisoformat(p.entry_date)).days
            if held >= p.horizon_days:
                out.append(sym)
        return out


# ---------------------------------------------------------------- checkpoint

def checkpoint_stats(closed: list) -> dict:
    """The frozen prereg metrics over closed trades."""
    import math

    def _get(t, name):
        return t[name] if isinstance(t, dict) else getattr(t, name)

    xs = [_get(t, "excess") for t in closed]
    n = len(xs)
    if n < 2:
        return {"n": n}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    t_stat = m / (sd / math.sqrt(n)) if sd else None
    rows = sorted(
        ((_get(t, "confidence"), x) for t, x in zip(closed, xs)),
        key=lambda r: r[0])
    k = max(1, n // 3)
    lo = sum(x for _, x in rows[:k]) / k
    hi = sum(x for _, x in rows[-k:]) / k
    return {"n": n, "mean_excess": round(m, 4),
            "t": round(t_stat, 2) if t_stat is not None else None,
            "win": round(sum(1 for x in xs if x > 0) / n, 2),
            "confidence_lo_tercile": round(lo, 4),
            "confidence_hi_tercile": round(hi, 4),
            "calibration_ok": hi >= lo}


def green_day_stats(curve: list) -> dict:
    """The daily-green scoreboard (operator mandate 2026-07-04).

    curve: list of {date, equity, spy} marks, oldest first. A day is
    green when equity rose vs the PRIOR mark. SPY's green-day rate over
    the same marks is computed beside it — a raw green rate means
    nothing without the tape's own base rate.
    """
    marks = [c for c in curve if c.get("equity")]
    if len(marks) < 2:
        return {"days": len(marks), "green_rate": None}
    greens = spys = 0
    streak = best_streak = 0
    for prev, cur in zip(marks, marks[1:]):
        if cur["equity"] > prev["equity"]:
            greens += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
        if cur.get("spy") and prev.get("spy") and cur["spy"] > prev["spy"]:
            spys += 1
    n = len(marks) - 1
    return {"days": n,
            "green_rate": round(greens / n, 3),
            "spy_green_rate": round(spys / n, 3),
            "current_streak": streak,
            "best_streak": best_streak}
