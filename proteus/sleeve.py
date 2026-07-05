"""Proteus live sleeve — the discretionary god's real-money book.

Proteus went live on 2026-07-04 (operator directive, before his first
paper trade): Midas's retired sleeve funds him. The journal discipline
is unchanged and lives in proteus.journal — every entry/exit still goes
through the validated writer FIRST. This module only keeps the money
honest:

- LONG ONLY. The broker cannot short; short expression is inverse/short
  ETFs, which are ordinary long positions here.
- No modeled fees or borrow. Fills are real; the fill price IS the cost.
- One position per symbol, no leverage: entries are capped by cash.
- Kill switch liquidates via ``liquidate_all`` like every other god.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date as _date
from typing import Optional

from proteus.journal import Position, ClosedTrade, JournalError

SLEEVE_PATH = "cache/proteus_sleeve.json"
JOURNAL_PATH = "cache/proteus_journal.jsonl"
CURVE_PATH = "cache/proteus_curve.json"
BELIEFS_PATH = "cache/proteus_beliefs.md"
LEDGER_PATH = "cache/proteus_ledger.jsonl"
CADENCE_PATH = "cache/proteus_cadence.json"

# Proteus is the TRUE experiment (operator directive 2026-07-05: "make him
# smart and greedy, not stupid"). There is deliberately NO hard per-position
# cap — he may concentrate as far as all-in if the conviction earns it. The
# two rails below don't limit his greed; they forbid the two ways a
# discretionary book blows up by ACCIDENT rather than by choice:
#   1. CONCENTRATION_ACK_PCT — a position past this fraction of the book is
#      allowed, but ONLY with an explicit, substantive risk acknowledgment.
#      Going big is his call; going big without naming the downside is not.
#   2. HALT_DRAWDOWN — a 40% drawdown from peak equity HALTS NEW ENTRIES
#      (it does NOT force-sell — his convex bets play out to their own kill
#      conditions; the kill switch remains the only forced-liquidation path).
#      The line between a greedy experiment and a stupid one is "don't dig the
#      hole deeper once you're already 40% down."
CONCENTRATION_ACK_PCT = 0.25   # past 25% of the book, a conscious ack is required
RISK_ACK_MIN_CHARS = 80        # the ack must name the worst case + why it's survivable
HALT_DRAWDOWN = 0.40           # 40% drawdown from peak halts NEW entries (no liquidation)


@dataclass
class LiveBook:
    cash: float = 0.0
    contributed_cash: float = 0.0
    positions: dict = field(default_factory=dict)    # symbol -> Position
    closed: list = field(default_factory=list)       # list[ClosedTrade]
    realized_pnl: float = 0.0
    halted: bool = False
    peak_equity: float = 0.0
    pending_funding: Optional[dict] = None
    name: str = "proteus"

    # -- persistence --
    @classmethod
    def load(cls, path: str = SLEEVE_PATH) -> "LiveBook":
        if not os.path.exists(path):
            return cls()
        raw = json.load(open(path))
        book = cls(
            cash=raw.get("cash", 0.0),
            contributed_cash=raw.get("contributed_cash", 0.0),
            realized_pnl=raw.get("realized_pnl", 0.0),
            halted=raw.get("halted", False),
            pending_funding=raw.get("pending_funding"),
        )
        # `or cash` heals a legacy null/absent peak; self-corrects upward on the
        # next update_peak and can't false-trip (equity >= cash == peak).
        book.peak_equity = float(raw.get("peak_equity") or raw.get("cash", 0.0))
        book.positions = {s: Position(**p) for s, p in raw.get("positions", {}).items()}
        book.closed = [ClosedTrade(**t) for t in raw.get("closed", [])]
        return book

    def save(self, path: str = SLEEVE_PATH) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        json.dump({
            "name": self.name,
            "cash": self.cash,
            "contributed_cash": self.contributed_cash,
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "closed": [asdict(t) for t in self.closed],
            "realized_pnl": self.realized_pnl,
            "halted": self.halted,
            "peak_equity": self.peak_equity,
            "trades_count": len(self.closed),
            "pending_funding": self.pending_funding,
        }, open(path, "w"), indent=1)

    # -- funding --
    def fund(self, *, amount: float, source: str, date: str, note: str = "") -> None:
        """Receive a capital transfer (e.g. the Midas sweep). Clears any
        pending_funding marker whose source matches."""
        if not (isinstance(amount, (int, float)) and amount > 0):
            raise JournalError(f"funding amount must be positive, got {amount!r}")
        self.cash += amount
        self.contributed_cash += amount
        pf = self.pending_funding or {}
        if pf.get("from") == source:
            self.pending_funding = None
        # advance the high-water mark to the funded cash so the breaker measures
        # drawdown from the real starting equity, not from 0.
        if self.cash > self.peak_equity:
            self.peak_equity = self.cash

    def is_funded(self) -> bool:
        return self.pending_funding is None and self.contributed_cash > 0

    # -- exposure math --
    def equity(self, marks: dict) -> float:
        """Cash + live value of longs. marks: symbol -> price."""
        eq = self.cash
        for sym, p in self.positions.items():
            eq += p.shares * float(marks.get(sym, p.entry_price))
        return eq

    # -- ruin breaker (halts NEW entries; never force-sells — see module note) --
    def update_peak(self, marks: Optional[dict] = None) -> None:
        eq = self.equity(marks or {})
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: Optional[dict] = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks or {}) / self.peak_equity)

    def check_halt(self, marks: Optional[dict] = None) -> bool:
        """Trip the breaker (set halted) if drawdown from peak >= HALT_DRAWDOWN.
        Halting blocks new entries only; existing positions are NOT liquidated
        (that is the kill switch's job) — Proteus's convex bets play out to
        their own journaled kill conditions."""
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    # -- trades (record ACTUAL broker fills; journal record comes first) --
    def enter(self, *, symbol: str, shares: float, price: float,
              date: str, spy_price: float, horizon_days: int,
              confidence: float, edge_class: str,
              risk_ack: str = "", equity: Optional[float] = None,
              marks: Optional[dict] = None) -> Position:
        symbol = symbol.upper()
        if self.halted:
            raise JournalError(
                "book is halted — no new entries (drawdown breaker tripped or kill switch)")
        if not self.is_funded():
            raise JournalError("book is not funded yet — research only")
        if symbol in self.positions:
            raise JournalError(f"{symbol}: already open — one position per symbol")
        dollars = shares * price
        if dollars > self.cash + 1e-6:
            raise JournalError(
                f"{symbol}: ${dollars:,.2f} exceeds cash ${self.cash:,.2f} — no leverage")
        # Conscious-concentration gate: NO hard cap — Proteus may size a name as
        # far as all-in if the conviction earns it. But past CONCENTRATION_ACK_PCT
        # of the book he must pass an explicit, substantive risk_ack naming the
        # worst case and why it's survivable. This forbids UNCONSCIOUS
        # concentration, not greed (operator directive 2026-07-05).
        # The denominator must be LIVE equity (bug-hunt 2026-07-05): equity({})
        # marks held names at stale entry prices, so a declining book could let
        # a >25% position slip past the gate un-acked. With open positions the
        # caller MUST supply live `marks` (or a live `equity`); a cash-only book
        # needs neither (cash IS live equity).
        if equity is not None:
            book_eq = float(equity)
        elif self.positions and marks is None:
            raise JournalError(
                "concentration gate needs LIVE equity: pass marks={sym: live_px} "
                "(or equity=) when the book holds positions — stale entry-price "
                "equity can wave a >25% position through un-acked")
        else:
            book_eq = self.equity(marks or {})
        frac = dollars / book_eq if book_eq > 0 else 1.0
        if frac > CONCENTRATION_ACK_PCT and len(risk_ack.strip()) < RISK_ACK_MIN_CHARS:
            raise JournalError(
                f"{symbol}: {frac:.0%} of the book is past the "
                f"{CONCENTRATION_ACK_PCT:.0%} conscious-concentration line — pass "
                f"risk_ack (>= {RISK_ACK_MIN_CHARS} chars) naming the worst-case loss "
                "and why it's survivable/justified. Going big is allowed; going big "
                "by accident is not.")
        self.cash -= dollars
        pos = Position(symbol=symbol, side="long", dollars=dollars,
                       shares=shares, entry_price=price,
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
        proceeds = p.shares * price
        self.cash += proceeds
        net_return = price / p.entry_price - 1
        spy_ret = spy_price / p.spy_entry - 1
        trade = ClosedTrade(
            symbol=symbol, side=p.side, dollars=p.dollars,
            entry_price=p.entry_price, exit_price=price,
            entry_date=p.entry_date, exit_date=date, exit_reason=exit_reason,
            net_return=round(net_return, 6), spy_return=round(spy_ret, 6),
            excess=round(net_return - spy_ret, 6),
            confidence=p.confidence, edge_class=p.edge_class,
            horizon_days=p.horizon_days,
        )
        self.closed.append(trade)
        self.realized_pnl += proceeds - p.dollars
        return trade

    def horizon_expired(self, today: str) -> list[str]:
        """Symbols whose declared horizon has elapsed — must exit this session."""
        out = []
        for sym, p in self.positions.items():
            held = (_date.fromisoformat(today) - _date.fromisoformat(p.entry_date)).days
            if held >= p.horizon_days:
                out.append(sym)
        return out

    def liquidate_all(self, marks: dict, today: str) -> list[tuple]:
        """Kill-switch path (shared.guards.liquidate_if_kill). Marks every
        position closed at the given prices; the caller places the actual
        broker sells and journals each exit."""
        sold = []
        for sym in list(self.positions.keys()):
            px = float(marks.get(sym, self.positions[sym].entry_price))
            spy = float(marks.get("SPY", self.positions[sym].spy_entry))
            shares = self.positions[sym].shares
            self.exit(symbol=sym, price=px, date=today,
                      spy_price=spy, exit_reason="kill_switch")
            sold.append((sym, shares, px))
        self.halted = True
        return sold
