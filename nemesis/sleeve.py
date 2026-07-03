"""NemesisSleeve — the gated live sleeve for the spinoff reader.

Nemesis v2 buys orphaned spincos AFTER the forced-seller dump and holds
~5 months while the market discovers them. This sleeve is the real-money
capability behind that: it exists in full — accounting, stops, cooldowns,
halt — even while NEMESIS_LIVE stays unset, because the exit rules must be
FROZEN before the first dollar. Written-in-advance rules beat tuned-later
rules (see the week of refutations in docs/); an exit policy invented while
staring at a losing position is not a policy, it is a mood.

Structure mirrors AchillesSleeve: standalone (does NOT inherit BaseSleeve),
positions keyed by symbol (what the trinity dashboard and shared.guards
already expect), T+1 settlements, GFV tracking, peak/halt. The differences
are the strategy: 5 slots instead of 12 (10-20 qualifying spins/yr at
~5-month holds means the basket turns slowly), a 150 CALENDAR day hold that
matches the ghost's grading horizon exactly (live and paper must measure
the same thesis, or the ghost's verdict says nothing about the sleeve), and
a -40% stop that is deliberately catastrophic-only — spinoffs chop near
their lows post-dump, and a tight stop would systematically evict normal
spinoff behavior. The floor exists for disasters, not risk-timing.

Exits are a closed vocabulary (EXIT_REASONS). An exit reason not in the
set raises — an unexplained exit is a rule violation, not a default —
because exit_reason_stats() is how we later learn which rules earned their
keep, and an ad-hoc reason string would silently fall out of that ledger.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Optional


# FROZEN constants — the parameters ARE the experiment. Changing any of
# them mid-sample invalidates every graded trade recorded before the
# change: a hit rate pooled across two different rule sets measures
# neither. New values require a new experiment with a fresh sample.
CAPITAL_BASE = 2_000.0
MAX_POSITIONS = 5        # 10-20 qualifying spins/yr at ~5-month holds
HOLD_DAYS = 150          # CALENDAR days — matches ghost HORIZON_DAYS so
                         # live and paper grade the same thesis
HARD_STOP_PCT = -0.40    # catastrophic-only; a tight stop evicts normal
                         # post-dump chop and destroys the strategy
HALT_DRAWDOWN = 0.40     # pantheon standard
FEE_BPS = 5
STOP_COOLDOWN_DAYS = 90  # a stopped spinoff is a one-shot event gone
                         # wrong, not a re-entry candidate

# Thesis-break exits require a WRITTEN case in the runbook — they are the
# human/LLM-judged counterparts to the mechanical stops, and due_exits()
# will never emit them. Each one is the Form 10 read being proven wrong:
THESIS_BREAK_REASONS = frozenset({
    "garbage_materialized",   # the dumped liabilities were real after all
    "going_concern",          # auditor doubt / bankruptcy risk disclosed
    "fraud",                  # SEC investigation or fraud allegation
    "delisting_risk",         # exchange non-compliance, no cure in sight
    "guidance_collapse",      # standalone economics far below pro-formas
})

# index_inclusion is the ONE early exit that is not a failure: the thesis
# is "forced sellers dump, then someone discovers the orphan" — selling
# INTO forced index BUYING is that discovery arriving ahead of schedule.
EXIT_REASONS = THESIS_BREAK_REASONS | {
    "time_stop", "hard_stop", "index_inclusion", "liquidation",
}


def _to_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def next_business_day(today: str) -> str:
    d = _to_date(today)
    while True:
        d = d + timedelta(days=1)
        if d.weekday() < 5:
            return d.strftime("%Y-%m-%d")


@dataclass
class NemesisPosition:
    """One spinco slot. The dossier tags (verdict/conviction/incentive_
    alignment/entry_window) ride on the position so the TradeResult cut at
    exit is self-contained for calibration — no join back to a dossier file
    that may have been rewritten since entry."""
    symbol: str
    shares: float
    entry_price: float
    entry_date: str
    stop_price: float     # entry * (1 + HARD_STOP_PCT)
    exit_date: str        # entry + HOLD_DAYS calendar days (ISO)
    verdict: Optional[str] = None
    conviction: Optional[float] = None
    incentive_alignment: Optional[float] = None
    entry_window: Optional[str] = None


@dataclass
class TradeResult:
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    exit_reason: str
    return_pct: float
    pnl: float
    verdict: Optional[str] = None
    conviction: Optional[float] = None
    incentive_alignment: Optional[float] = None
    entry_window: Optional[str] = None


@dataclass
class Settlement:
    settle_date: str
    amount: float


class NemesisSleeve:

    def __init__(self, initial_cash: float = CAPITAL_BASE):
        self.name = "nemesis"
        self.cash: float = float(initial_cash)
        self.positions: dict[str, NemesisPosition] = {}
        self.peak_equity: float = float(initial_cash)
        self.realized_pnl: float = 0.0
        self.trades_count: int = 0
        self.halted: bool = False
        self.contributed_cash: float = float(initial_cash)
        self.pending_settlements: list[Settlement] = []
        self.gfv_count: int = 0
        self.cooldowns: dict[str, str] = {}
        self.trade_results: list[TradeResult] = []

    # ------- accounting -------

    def equity(self, marks: Optional[dict[str, float]] = None) -> float:
        marks = marks or {}
        total = self.cash
        for sym, pos in self.positions.items():
            px = marks.get(sym, pos.entry_price)
            total += pos.shares * px
        return total

    def update_peak(self, marks: Optional[dict[str, float]] = None) -> None:
        eq = self.equity(marks)
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks: Optional[dict[str, float]] = None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks) / self.peak_equity)

    def check_halt(self, marks: Optional[dict[str, float]] = None) -> bool:
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    def inject(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("inject() requires non-negative amount")
        self.cash += amount
        self.contributed_cash += amount

    def unsettled_cash(self, today: str) -> float:
        return sum(s.amount for s in self.pending_settlements if s.settle_date > today)

    def settled_cash(self, today: str) -> float:
        return self.cash - self.unsettled_cash(today)

    def process_settlements(self, today: str) -> None:
        self.pending_settlements = [
            s for s in self.pending_settlements if s.settle_date > today
        ]

    def in_cooldown(self, symbol: str, today: str) -> bool:
        until = self.cooldowns.get(symbol.upper())
        if not until:
            return False
        return today < until

    # ------- sizing -------

    def open_slots(self) -> int:
        return max(0, MAX_POSITIONS - len(self.positions))

    def target_dollars(self, marks: Optional[dict[str, float]] = None) -> float:
        """Equal-weight target per slot: total equity / MAX_POSITIONS.

        Every spinco gets the same weight regardless of conviction — the
        conviction score's job is to be GRADED (does it predict returns?),
        not to size positions before it has earned that right.
        """
        return self.equity(marks) / MAX_POSITIONS

    def holds(self, symbol: str) -> bool:
        return symbol.upper() in self.positions

    # ------- trading -------

    def enter(
        self,
        symbol: str,
        shares: float,
        price: float,
        today: str,
        *,
        verdict: str,
        conviction: float,
        incentive_alignment: float,
        entry_window: str,
    ) -> bool:
        """Open a spinco slot. The dossier tags are keyword-REQUIRED: a live
        Nemesis entry without a written Form 10 read is not this strategy's
        trade, and a TradeResult without tags is ungradeable."""
        sym = symbol.upper()
        if self.halted:
            return False
        if sym in self.positions:
            return False  # one slot per spinco — no doubling up
        if len(self.positions) >= MAX_POSITIONS:
            return False  # basket full
        if shares <= 0 or price <= 0:
            return False
        if self.in_cooldown(sym, today):
            return False

        dollars = shares * price
        fee = dollars * FEE_BPS / 10_000
        total_cost = dollars + fee
        if total_cost > self.cash + 1e-9:
            return False

        if total_cost > self.settled_cash(today) + 1e-9:
            self.gfv_count += 1

        stop_price = round(price * (1.0 + HARD_STOP_PCT), 4)
        exit_date = (_to_date(today) + timedelta(days=HOLD_DAYS)).strftime("%Y-%m-%d")

        self.positions[sym] = NemesisPosition(
            symbol=sym,
            shares=shares,
            entry_price=price,
            entry_date=today,
            stop_price=stop_price,
            exit_date=exit_date,
            verdict=verdict,
            conviction=conviction,
            incentive_alignment=incentive_alignment,
            entry_window=entry_window,
        )
        self.cash -= total_cost
        self.trades_count += 1
        return True

    def exit(self, symbol: str, price: float, today: str, reason: str) -> Optional[float]:
        """Close a slot. `reason` MUST come from EXIT_REASONS — an
        unexplained exit is a rule violation, not a default, so an unknown
        reason raises instead of being quietly recorded."""
        if reason not in EXIT_REASONS:
            raise ValueError(
                f"unknown exit reason {reason!r}; must be one of {sorted(EXIT_REASONS)}"
            )
        sym = symbol.upper()
        pos = self.positions.get(sym)
        if pos is None or price <= 0:
            return None

        proceeds = pos.shares * price
        fee = proceeds * FEE_BPS / 10_000
        net = proceeds - fee
        cost = pos.shares * pos.entry_price
        realized = net - cost
        return_pct = (price - pos.entry_price) / pos.entry_price

        self.realized_pnl += realized
        self.cash += net
        self.pending_settlements.append(Settlement(next_business_day(today), net))

        self.trade_results.append(TradeResult(
            symbol=pos.symbol,
            entry_date=pos.entry_date,
            entry_price=pos.entry_price,
            exit_date=today,
            exit_price=price,
            exit_reason=reason,
            return_pct=return_pct,
            pnl=realized,
            verdict=pos.verdict,
            conviction=pos.conviction,
            incentive_alignment=pos.incentive_alignment,
            entry_window=pos.entry_window,
        ))

        # A stop or a thesis break means the one-shot event went wrong —
        # the spinco is not a re-entry candidate for a quarter. time_stop
        # and index_inclusion are the thesis COMPLETING, so no cooldown;
        # liquidation is an operator action, not a verdict on the name.
        if reason == "hard_stop" or reason in THESIS_BREAK_REASONS:
            cooldown_end = _to_date(today) + timedelta(days=STOP_COOLDOWN_DAYS)
            self.cooldowns[sym] = cooldown_end.strftime("%Y-%m-%d")

        del self.positions[sym]
        return realized

    def due_exits(self, quotes: dict[str, float], today: str) -> list[tuple[str, str]]:
        """Which positions the MECHANICAL rules say to exit now, and why.

        hard_stop takes precedence over time_stop: if both fire on the same
        day, the -40% floor is the reason we are leaving. Thesis breaks are
        NEVER auto-detected here — they require a written case in the
        runbook, because "garbage_materialized" is a judgment about a
        filing, not a price level."""
        out = []
        for sym, pos in self.positions.items():
            px = quotes.get(sym)
            if px is not None and px <= pos.stop_price:
                out.append((sym, "hard_stop"))
            elif today >= pos.exit_date:
                out.append((sym, "time_stop"))
        return out

    def liquidate(self, marks: dict[str, float], today: str) -> float:
        """Exit every open position (kill switch / operator liquidation).

        Bypasses the halt flag: the halt exists to stop NEW risk, and must
        never trap the operator inside existing risk."""
        was_halted = self.halted
        self.halted = False
        total = 0.0
        try:
            for sym in list(self.positions):
                px = marks.get(sym, self.positions[sym].entry_price)
                r = self.exit(sym, px, today, "liquidation")
                if r is not None:
                    total += r
        finally:
            self.halted = was_halted
        return total

    # ------- calibration -------

    def graded_count(self) -> int:
        return len(self.trade_results)

    def hit_rate(self) -> Optional[float]:
        if not self.trade_results:
            return None
        hits = sum(1 for r in self.trade_results if r.return_pct > 0)
        return hits / len(self.trade_results)

    def avg_return(self) -> Optional[float]:
        if not self.trade_results:
            return None
        return sum(r.return_pct for r in self.trade_results) / len(self.trade_results)

    def verdict_stats(self) -> dict[str, dict]:
        """Per-verdict outcomes: does the Form 10 read predict returns?

        This is the live-sleeve echo of the ghost's verdict_groups — if
        "own" and "watch" trades perform alike, the reading is theater."""
        groups: dict[str, list[float]] = {}
        for r in self.trade_results:
            key = r.verdict if r.verdict is not None else "untagged"
            groups.setdefault(key, []).append(r.return_pct)
        return {
            v: {
                "n": len(rets),
                "mean_return": sum(rets) / len(rets),
                "hit_rate": sum(1 for x in rets if x > 0) / len(rets),
            }
            for v, rets in groups.items()
        }

    def exit_reason_stats(self) -> dict[str, dict]:
        """Per-reason outcomes: which FROZEN exit rules earned their keep?

        This table is the only honest way to revisit the rules later —
        after a full sample, not mid-sample."""
        groups: dict[str, list[float]] = {}
        for r in self.trade_results:
            groups.setdefault(r.exit_reason, []).append(r.return_pct)
        return {
            reason: {
                "n": len(rets),
                "mean_return": sum(rets) / len(rets),
            }
            for reason, rets in groups.items()
        }

    # ------- persistence -------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "cash": self.cash,
            "positions": {sym: asdict(pos) for sym, pos in self.positions.items()},
            "peak_equity": self.peak_equity,
            "realized_pnl": self.realized_pnl,
            "trades_count": self.trades_count,
            "halted": self.halted,
            "contributed_cash": self.contributed_cash,
            "pending_settlements": [asdict(s) for s in self.pending_settlements],
            "gfv_count": self.gfv_count,
            "cooldowns": dict(self.cooldowns),
            "trade_results": [asdict(r) for r in self.trade_results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NemesisSleeve":
        s = cls(initial_cash=0.0)
        s.cash = float(data["cash"])
        # Dataclass defaults tolerate files written before a tag existed —
        # an old position loads with the tag as None rather than crashing
        # the hydrate path.
        s.positions = {
            sym.upper(): NemesisPosition(**pos)
            for sym, pos in data.get("positions", {}).items()
        }
        s.peak_equity = float(data.get("peak_equity", s.cash))
        s.realized_pnl = float(data.get("realized_pnl", 0.0))
        s.trades_count = int(data.get("trades_count", 0))
        s.halted = bool(data.get("halted", False))
        s.contributed_cash = float(data.get("contributed_cash", s.cash))
        s.pending_settlements = [Settlement(**x) for x in data.get("pending_settlements", [])]
        s.gfv_count = int(data.get("gfv_count", 0))
        s.cooldowns = dict(data.get("cooldowns", {}))
        s.trade_results = [TradeResult(**r) for r in data.get("trade_results", [])]
        return s

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: str) -> "NemesisSleeve":
        with open(path) as f:
            return cls.from_dict(json.load(f))
