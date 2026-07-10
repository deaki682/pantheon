"""HermesBook — the live merger-arb book (Arm A, real money).

Holds several concurrent cash-merger positions. Each is a bet with a bounded
CONTRACTUAL floor (the deal-break), so ruin risk is controlled by two rules
that never bend:
  - PER_DEAL_CAP: no single deal above a hard % of equity (one break survivable).
  - book-level break exposure kept so the worst plausible round (a break on the
    largest position) stays inside the convexity bar (~-12% book).

Long-only, no leverage, no options (a cash deal needs no acquirer short — you
just buy the target). Funded by a small dedicated sleeve at arming; the LLM's
keep/drop verdict for each deal lives in hermes.ab (the A/B), not here — this
module only keeps the real money honest.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict, field
from datetime import date as _date
from typing import Optional

from shared.guards import OrderRecord, append_order, already_placed_today, read_ledger

SLEEVE_PATH = "cache/hermes_sleeve.json"
LEDGER_PATH = "cache/hermes_ledger.jsonl"
CURVE_PATH = "cache/hermes_curve.json"

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

PER_DEAL_CAP = 0.15        # no single deal above 15% of equity
MAX_CONCURRENT = 10        # diversify across deals; one break must be survivable
BREAK_STOP_PCT = 0.15      # exit if the target falls 15% below entry (deal-break signature)
CASH_RESERVE = 0.02        # keep 2% cash
HALT_DRAWDOWN = 0.40       # 40% drawdown from peak halts new entries (pantheon standard)
MIN_SPREAD = 0.01          # refuse a NEW entry with <1% remaining to the offer — the
                           # arb edge is spent (or it's trading at/above offer = topping-
                           # bid speculation, not arb). The "already fired" guard, event side.


class HermesError(Exception):
    pass


@dataclass
class DealPosition:
    symbol: str
    shares: float
    entry_price: float
    offer_price: float          # the contractual cash consideration per share
    entry_date: str
    expected_close: str         # target resolution date (best estimate)
    break_stop: float           # exit level = entry_price * (1 - BREAK_STOP_PCT)
    spy_entry: float
    deal_type: str = "cash"
    dollars: float = 0.0

    def spread(self) -> float:
        """Remaining spread to the offer at entry (the base return if it closes)."""
        return self.offer_price / self.entry_price - 1.0 if self.entry_price > 0 else 0.0


@dataclass
class ClosedDeal:
    symbol: str
    entry_price: float
    exit_price: float
    entry_date: str
    exit_date: str
    net_return: float
    spy_return: float
    excess: float
    outcome: str                # "completed" | "broke" | "topping_bid" | "manual"
    dollars: float = 0.0


@dataclass
class HermesBook:
    cash: float = 0.0
    contributed_cash: float = 0.0
    positions: dict = field(default_factory=dict)   # symbol -> DealPosition
    closed: list = field(default_factory=list)      # list[ClosedDeal]
    realized_pnl: float = 0.0
    halted: bool = False
    peak_equity: float = 0.0
    pending_funding: Optional[dict] = None
    name: str = "hermes"

    # -- persistence --
    @classmethod
    def load(cls, path: str = SLEEVE_PATH) -> "HermesBook":
        if not os.path.exists(path):
            return cls()
        raw = json.load(open(path))
        b = cls(cash=raw.get("cash", 0.0), contributed_cash=raw.get("contributed_cash", 0.0),
                realized_pnl=raw.get("realized_pnl", 0.0), halted=raw.get("halted", False),
                pending_funding=raw.get("pending_funding"))
        b.peak_equity = float(raw.get("peak_equity") or raw.get("cash", 0.0))
        b.positions = {s: DealPosition(**p) for s, p in raw.get("positions", {}).items()}
        b.closed = [ClosedDeal(**t) for t in raw.get("closed", [])]
        return b

    def save(self, path: str = SLEEVE_PATH) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        json.dump({
            "name": self.name, "cash": self.cash, "contributed_cash": self.contributed_cash,
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "closed": [asdict(t) for t in self.closed], "realized_pnl": self.realized_pnl,
            "halted": self.halted, "peak_equity": self.peak_equity,
            "pending_funding": self.pending_funding,
            "trades_count": len(self.closed),
        }, open(path, "w"), indent=1)

    # -- funding --
    def fund(self, *, amount: float, source: str, date: str, note: str = "") -> None:
        if not (isinstance(amount, (int, float)) and amount > 0):
            raise HermesError(f"funding must be positive, got {amount!r}")
        self.cash += amount
        self.contributed_cash += amount
        pf = self.pending_funding or {}
        if pf.get("from") == source:
            self.pending_funding = None
        if self.cash > self.peak_equity:
            self.peak_equity = self.cash

    def is_funded(self) -> bool:
        return self.pending_funding is None and self.contributed_cash > 0

    def equity(self, marks: dict) -> float:
        eq = self.cash
        for s, p in self.positions.items():
            eq += p.shares * float(marks.get(s, p.entry_price))
        return eq

    # -- ruin breaker (parity with the rest of the roster; halts new entries) --
    def update_peak(self, marks: Optional[dict] = None) -> None:
        eq = self.equity(marks or {})
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: Optional[dict] = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks or {}) / self.peak_equity)

    def check_halt(self, marks: Optional[dict] = None) -> bool:
        """Trip the breaker (halt new entries) if drawdown from peak >=
        HALT_DRAWDOWN. Existing deals are not liquidated — each already carries
        its own contractual break-stop."""
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    # -- sizing: the ruin guard --
    def max_deal_dollars(self, equity: float) -> float:
        return PER_DEAL_CAP * equity

    def can_enter(self, symbol: str, dollars: float, equity: float,
                  today: Optional[str] = None,
                  ledger_path: str = LEDGER_PATH) -> tuple[bool, str]:
        if self.halted:
            return False, "book halted"
        if not self.is_funded():
            return False, "not funded"
        if symbol in self.positions:
            return False, "already open (one position per deal)"
        if len(self.positions) >= MAX_CONCURRENT:
            return False, f"at max concurrent deals ({MAX_CONCURRENT})"
        if dollars > self.cash * (1 - CASH_RESERVE) + 1e-6:
            return False, "exceeds available cash"
        if dollars > self.max_deal_dollars(equity) + 1e-6:
            return False, f"exceeds per-deal cap ({PER_DEAL_CAP:.0%} of equity)"
        # Ledger-aware duplicate guard (audit 2026-07-10: the incident's morning
        # buys were IN the ledger when the auto-run re-bought them — the sleeve
        # was the corrupted state, the ledger was the honest one; consult it).
        if today and os.path.exists(ledger_path) and already_placed_today(
                read_ledger(ledger_path), symbol, "buy", today):
            return False, f"a {symbol} buy is already in the ledger today — reconcile before re-entering"
        return True, "ok"

    # -- trades (record ACTUAL broker fills; journal/A-B record comes first) --
    # ATOMIC DOOR (audit 2026-07-10, the incident's root cause): when an
    # `order_id` is passed, enter/exit append the ledger row AND save the sleeve
    # to disk inside the same call — an order can no longer exist at the broker
    # with the sleeve un-mutated on disk (the state the auto-run exploited).
    # Paper/test paths omit order_id and touch no files.
    def enter(self, *, symbol: str, shares: float, price: float, offer_price: float,
              date: str, expected_close: str, spy_price: float, equity: float,
              deal_type: str = "cash", order_id: Optional[str] = None,
              sleeve_path: str = SLEEVE_PATH, ledger_path: str = LEDGER_PATH) -> DealPosition:
        symbol = symbol.upper()
        if deal_type != "cash":
            raise HermesError(
                f"{symbol}: deal_type {deal_type!r} refused — Hermes trades CASH "
                "mergers only (a stock deal has no contractual dollar floor)")
        if not _ISO_DATE.match(expected_close or ""):
            raise HermesError(
                f"{symbol}: expected_close {expected_close!r} must be ISO YYYY-MM-DD "
                "(best estimate; 'Q3 2026'-style strings made past_close() inert — audit 2026-07-10)")
        dollars = shares * price
        ok, why = self.can_enter(symbol, dollars, equity, today=date, ledger_path=ledger_path)
        if not ok:
            raise HermesError(f"{symbol}: cannot enter — {why}")
        spread = offer_price / price - 1.0 if price > 0 else -1.0
        if spread < MIN_SPREAD:
            raise HermesError(
                f"{symbol}: remaining spread {spread:.1%} below the {MIN_SPREAD:.0%} "
                "minimum — no arb edge left (at/above offer = topping-bid speculation)")
        self.cash -= dollars
        pos = DealPosition(symbol=symbol, shares=shares, entry_price=price,
                           offer_price=offer_price, entry_date=date,
                           expected_close=expected_close,
                           break_stop=round(price * (1 - BREAK_STOP_PCT), 4),
                           spy_entry=spy_price, deal_type=deal_type, dollars=dollars)
        self.positions[symbol] = pos
        if order_id is not None:
            append_order(ledger_path, OrderRecord(
                order_id=order_id, symbol=symbol, side="buy", dollars=dollars,
                date=date, shares=shares, price=price, status="filled"))
            self.save(sleeve_path)
        return pos

    def exit(self, *, symbol: str, price: float, date: str, spy_price: float,
             outcome: str, order_id: Optional[str] = None,
             sleeve_path: str = SLEEVE_PATH, ledger_path: str = LEDGER_PATH) -> ClosedDeal:
        symbol = symbol.upper()
        if symbol not in self.positions:
            raise HermesError(f"{symbol}: no open deal to exit")
        p = self.positions.pop(symbol)
        proceeds = p.shares * price
        self.cash += proceeds
        net = price / p.entry_price - 1.0
        spy_ret = spy_price / p.spy_entry - 1.0 if p.spy_entry else 0.0
        t = ClosedDeal(symbol=symbol, entry_price=p.entry_price, exit_price=price,
                       entry_date=p.entry_date, exit_date=date, net_return=round(net, 6),
                       spy_return=round(spy_ret, 6), excess=round(net - spy_ret, 6),
                       outcome=outcome, dollars=p.dollars)
        self.closed.append(t)
        self.realized_pnl += proceeds - p.dollars
        if order_id is not None:
            append_order(ledger_path, OrderRecord(
                order_id=order_id, symbol=symbol, side="sell", dollars=proceeds,
                date=date, shares=p.shares, price=price, status="filled"))
            self.save(sleeve_path)
        return t

    def break_triggered(self, marks: dict) -> list[str]:
        """Symbols whose price has fallen through the break-stop — MUST exit
        (don't ride a broken deal down)."""
        out = []
        for s, p in self.positions.items():
            px = float(marks.get(s, p.entry_price))
            if px <= p.break_stop:
                out.append(s)
        return out

    def past_close(self, today: str) -> list[str]:
        """Deals past their expected close date that haven't resolved — flag for
        a manual look (deal delayed, or the close/delist needs reconciling).
        An UNPARSEABLE expected_close is also flagged (audit 2026-07-10: 'Q3
        2026'-style strings compared lexicographically > any ISO date, so a
        stalled deal would never get its mandated look)."""
        out = []
        for s, p in self.positions.items():
            ec = p.expected_close or ""
            if not _ISO_DATE.match(ec):
                out.append(s)          # unintelligible date = needs a look, not a skip
            elif ec < today:
                out.append(s)
        return out

    def missing_marks(self, marks: dict) -> list[str]:
        """Open positions with NO quote in `marks`. equity()/break_triggered()
        fall back to entry_price for a missing mark, which silently shows zero
        loss (audit 2026-07-10) — the tend liturgy must treat a non-empty result
        here as a must-refetch before trusting any breaker/break-stop answer."""
        return [s for s in self.positions if s not in marks]

    def liquidate_all(self, marks: dict, today: str) -> list[tuple]:
        """Kill-switch path."""
        sold = []
        for s in list(self.positions.keys()):
            px = float(marks.get(s, self.positions[s].entry_price))
            spy = float(marks.get("SPY", self.positions[s].spy_entry))
            shares = self.positions[s].shares
            self.exit(symbol=s, price=px, date=today, spy_price=spy, outcome="kill_switch")
            sold.append((s, shares, px))
        self.halted = True
        return sold


def hermes_reconcile(book: HermesBook, broker_shares: dict,
                     ledger_path: str = LEDGER_PATH) -> list[str]:
    """TWO-SIDED, Hermes-scoped reconcile (audit 2026-07-10). The house-wide
    `pre_trade_check` is deliberately one-sided — `broker > sleeve` is waved
    through as personal overlap — but that excuse NEVER applies to a symbol in
    Hermes's own ledger: god-bought shares the sleeve doesn't know about are
    exactly the orders-ledgered-but-not-sleeved incident state. Returns a list
    of human-readable mismatches; the runbook refuses ALL new entries while it
    is non-empty. Legacy ledger rows without fill shares are noted, not guessed."""
    problems: list[str] = []
    net: dict = {}
    legacy: set = set()
    if os.path.exists(ledger_path):
        for line in open(ledger_path):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"ledger: unparseable row {line[:60]!r}")
                continue
            sym = (r.get("symbol") or "").upper()
            if not sym or r.get("status") == "cancelled":
                continue
            sh = r.get("shares")
            if sh is None:
                legacy.add(sym)     # placement-notional row; can't replay shares
                continue
            net[sym] = net.get(sym, 0.0) + (float(sh) if r.get("side") == "buy" else -float(sh))
    for sym in sorted(set(net) | set(book.positions)):
        sleeve_sh = book.positions[sym].shares if sym in book.positions else 0.0
        if sym in net and abs(net[sym] - sleeve_sh) > 1e-4:
            problems.append(
                f"{sym}: ledger net {net[sym]:.4f} sh != sleeve {sleeve_sh:.4f} sh")
        broker_sh = float(broker_shares.get(sym, 0.0))
        if sleeve_sh - broker_sh > 1e-4:
            problems.append(f"{sym}: sleeve {sleeve_sh:.4f} sh > broker {broker_sh:.4f} sh (missing shares)")
        if sym not in legacy and sym in net and broker_sh - max(sleeve_sh, 0.0) > 1e-4 \
                and broker_sh - net.get(sym, 0.0) > 1e-4:
            problems.append(
                f"{sym}: broker {broker_sh:.4f} sh exceeds both sleeve and ledger — "
                "god-bought shares unaccounted for (the incident signature)")
    return problems
