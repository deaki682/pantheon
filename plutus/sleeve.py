"""PlutusSleeve — net-issuance capital-return god (LIVE 2026-07-06).

Same book-keeping core as Delphi (BaseSleeve: cash, positions, T+1
settlement, equity), plus the two things a launched-live god needs:

- **Funding provenance.** Plutus is seeded by Delphi's retiring sleeve, not
  an ``initial_cash`` at birth. He starts with ``pending_funding`` set and
  ``cash == 0``; the Delphi wind-down sweep calls ``fund()`` (same shape as
  proteus.sleeve.LiveBook.fund) which injects the cash and clears the
  marker. ``is_funded()`` gates the first live rebalance — sessions before
  the sweep lands are research-only, exactly like Proteus.
- **40% circuit breaker.** Peak-equity high-water mark and ``check_halt``,
  identical to Delphi/Midas — the one non-negotiable risk control the
  launch override committed to.

No cooldown (quarterly rebalance is slow by construction; the churn that
sank Delphi is structurally absent). Equal-weight ~2%/name across 50 names.
"""
from __future__ import annotations

from typing import Optional

from shared.base_sleeve import BaseSleeve


N_POSITIONS = 50
PER_NAME_CAP = 0.05        # 50 names ~2% each; 5% is a generous safety ceiling
CASH_FLOOR = 0.02
MIN_TICKET = 5.0           # sub-$2k book / 50 names => small tickets; allow them
REBAL_BAND = 0.20          # only trade a name that has drifted >20% from target
HALT_DRAWDOWN = 0.40       # 40% drawdown from peak equity trips the breaker


class PlutusSleeve(BaseSleeve):
    cooldown_days = 0       # quarterly cadence; no per-name cooldown

    def __init__(self, name: str = "plutus", initial_cash: float = 0.0):
        # Plutus is funded by transfer, not birth cash: default 0. contributed
        # starts at 0 too so is_funded() is honest until the sweep lands.
        super().__init__(name=name, initial_cash=initial_cash)
        self.contributed_cash = float(initial_cash)
        self.peak_equity: float = float(initial_cash)
        # {"from": "delphi", "expected": ..., "directive_date": ..., "note": ...}
        # or None once funded. Set at scaffolding; cleared by fund().
        self.pending_funding: Optional[dict] = None

    # ------- funding (mirrors proteus.sleeve.LiveBook.fund) -------

    def fund(self, *, amount: float, source: str, date: str, note: str = "") -> None:
        """Receive a capital transfer (the Delphi retirement sweep). Injects
        cash + contributed and clears any pending_funding whose source matches.
        """
        if not (isinstance(amount, (int, float)) and amount > 0):
            raise ValueError(f"funding amount must be positive, got {amount!r}")
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

    # ------- circuit breaker (identical semantics to Delphi/Midas) -------

    def update_peak(self, marks=None) -> None:
        eq = self.equity(marks)
        if eq > self.peak_equity:
            self.peak_equity = eq

    def absolute_drawdown(self, marks=None) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, 1.0 - self.equity(marks) / self.peak_equity)

    def check_halt(self, marks=None) -> bool:
        """Trip the breaker (set halted) if drawdown >= HALT_DRAWDOWN."""
        if self.absolute_drawdown(marks) >= HALT_DRAWDOWN - 1e-9:
            self.halted = True
            return True
        return False

    # ------- persistence (extend base to carry peak + funding marker) -------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["peak_equity"] = self.peak_equity
        d["pending_funding"] = self.pending_funding
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PlutusSleeve":
        s = super().from_dict(data)
        # `or s.cash` heals a legacy null/absent peak; self-corrects upward on
        # the next update_peak and can't false-trip (equity >= cash = peak).
        s.peak_equity = float(data.get("peak_equity") or s.cash)  # type: ignore[attr-defined]
        s.pending_funding = data.get("pending_funding")  # type: ignore[attr-defined]
        return s
