"""Ghost Oracle — a paper-only, unconstrained-breadth shadow built for learning.

The real Oracle holds ~8 names with real money, so it produces far too few
graded outcomes to ever measure whether its signals work. Ghost Oracle runs the
same screen/dossier brain but optimizes for DATA instead of returns: it opens a
paper position for EVERY candidate — no concentration, no min-ticket, no caps —
grades each one's forward return at its horizon, and reports what the signals
are actually worth (lens predictiveness, conviction calibration, hit rate).

Design notes:
  - No sleeve, no broker, no real money. A position is just an entry in a ledger;
    "holding as many as possible" means recording every candidate.
  - Each entry is a labeled training example: features at entry (which lenses
    fired, quality, conviction) -> forward return at grade time.
  - Equal-notional by construction: each entry contributes one raw return sample,
    so the mean return is an equal-weight read and per-name signal is unbiased.
  - Pure + injectable: price lookups are passed in, so tests run offline.

Survivorship guard: a name that can't be priced at grade time (delisted/halted)
is graded as a loss (`delisted_return`, default -100%) rather than dropped — else
the stats would only ever see survivors and flatter the result.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

PriceLookup = Callable[[str], Optional[float]]


@dataclass
class GhostEntry:
    symbol: str
    entry_date: str           # YYYY-MM-DD
    entry_price: float
    horizon_days: int
    source: str               # "screen" | "dossier"
    features: dict = field(default_factory=dict)
    exit_date: str = ""
    exit_price: float = 0.0
    graded_return: Optional[float] = None  # None until graded

    @property
    def graded(self) -> bool:
        return self.graded_return is not None


# ------- Open paper positions (unconstrained breadth) -------

def open_entries(
    candidates: Iterable[dict],
    existing: Iterable[GhostEntry] = (),
    *,
    today: str,
    default_horizon_days: int = 365,
) -> list[GhostEntry]:
    """Build a paper entry for every priced candidate. No sizing, no caps.

    A candidate is {symbol, price, source?, horizon_days?, features?}. Names with
    no symbol or a non-positive price are skipped. Same-day re-opens of the same
    (symbol, source) are de-duped so one run can't double-count.
    """
    seen = {(e.symbol, e.source, e.entry_date) for e in existing}
    out: list[GhostEntry] = []
    for c in candidates:
        sym = (c.get("symbol") or "").upper()
        try:
            price = float(c.get("price") or 0.0)
        except (TypeError, ValueError):
            price = 0.0
        if not sym or price <= 0:
            continue
        source = c.get("source", "screen")
        key = (sym, source, today)
        if key in seen:
            continue
        seen.add(key)
        out.append(GhostEntry(
            symbol=sym,
            entry_date=today,
            entry_price=price,
            horizon_days=int(c.get("horizon_days") or default_horizon_days),
            source=source,
            features=dict(c.get("features") or {}),
        ))
    return out


# ------- Grade matured positions -------

def _horizon_reached(entry: GhostEntry, today: str) -> bool:
    try:
        due = datetime.strptime(entry.entry_date, "%Y-%m-%d") + timedelta(days=entry.horizon_days)
        return datetime.strptime(today, "%Y-%m-%d") >= due
    except ValueError:
        return False


def grade_entries(
    entries: Iterable[GhostEntry],
    price_lookup: PriceLookup,
    *,
    today: str,
    delisted_return: float = -1.0,
) -> int:
    """Grade every ungraded entry whose horizon has elapsed. Returns count graded.

    A name that can't be priced is graded as `delisted_return` (survivorship guard).
    """
    graded = 0
    for e in entries:
        if e.graded or not _horizon_reached(e, today):
            continue
        px = price_lookup(e.symbol)
        if px is None or px <= 0:
            e.exit_price = 0.0
            e.graded_return = delisted_return
        else:
            e.exit_price = float(px)
            e.graded_return = (e.exit_price / e.entry_price - 1.0) if e.entry_price > 0 else 0.0
        e.exit_date = today
        graded += 1
    return graded


# ------- Calibration: what are the signals actually worth? -------

def _mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def calibration_report(entries: Iterable[GhostEntry]) -> dict:
    """Summarize graded outcomes into signal-quality stats.

    Reports overall mean return + hit rate, per-lens lift (mean return when a
    boolean feature fired vs not), and conviction-tier means + monotonicity.
    """
    graded = [e for e in entries if e.graded]
    n = len(graded)
    if not n:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "lens_lift": {}, "conviction_tiers": {}, "conviction_monotonic": False}

    rets = [e.graded_return for e in graded]
    mean_return = sum(rets) / n
    hit_rate = sum(1 for r in rets if r > 0) / n

    # Per-lens lift: only boolean features (the lens flags).
    bool_flags = sorted({k for e in graded for k, v in e.features.items() if isinstance(v, bool)})
    lens_lift: dict[str, dict] = {}
    for f in bool_flags:
        # Compare only names where this lens was actually evaluated: True vs
        # explicit False. Entries missing the key (e.g. dossier-sourced rows that
        # never carried lens flags) are excluded so they can't pollute the lift.
        on = [e.graded_return for e in graded if e.features.get(f) is True]
        off = [e.graded_return for e in graded if e.features.get(f) is False]
        m_on, m_off = _mean(on), _mean(off)
        lens_lift[f] = {
            "n_on": len(on), "mean_on": m_on,
            "n_off": len(off), "mean_off": m_off,
            "lift": (m_on - m_off) if (m_on is not None and m_off is not None) else None,
        }

    # Conviction tiers (dossier-sourced entries carry a numeric conviction).
    from .learning import conviction_tier
    tiers: dict[str, list[float]] = {"high": [], "mid": [], "low": []}
    for e in graded:
        conv = e.features.get("conviction")
        if conv is None:
            continue
        tiers[conviction_tier(float(conv))].append(e.graded_return)
    tier_means = {t: _mean(v) for t, v in tiers.items()}
    present = [t for t in ("high", "mid", "low") if tiers[t]]
    monotonic = len(present) >= 2 and all(
        tier_means[present[i]] >= tier_means[present[i + 1]] for i in range(len(present) - 1)
    )

    return {
        "n": n,
        "mean_return": mean_return,
        "hit_rate": hit_rate,
        "lens_lift": lens_lift,
        "conviction_tiers": {t: {"n": len(tiers[t]), "mean": tier_means[t]} for t in tiers},
        "conviction_monotonic": monotonic,
    }


# ------- Adapters: screen rows / dossiers -> candidates -------

def screen_rows_to_candidates(
    rows: Iterable[dict], price_lookup: PriceLookup, *, horizon_days: int = 365,
) -> list[dict]:
    """Turn `oracle_screen.json` `top` rows into priced candidates.

    Features = the row's lens flags (so lens lift is measurable). Names that
    can't be priced are dropped at open time (they never enter the ledger).
    """
    out: list[dict] = []
    for r in rows:
        sym = (r.get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        feats = dict(r.get("lenses") or {})
        feats["score"] = r.get("score")
        out.append({"symbol": sym, "price": float(px), "horizon_days": horizon_days,
                    "source": "screen", "features": feats})
    return out


def dossiers_to_candidates(
    dossiers: Iterable[dict], price_lookup: Optional[PriceLookup] = None,
    *, default_horizon_days: int = 365,
) -> list[dict]:
    """Turn dossiers into priced candidates carrying their conviction as a feature."""
    out: list[dict] = []
    for d in dossiers:
        sym = (d.get("symbol") or "").upper()
        if not sym:
            continue
        px = d.get("current_price")
        if (px is None or float(px) <= 0) and price_lookup:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        hd = int(round(float(d.get("horizon_years", 1.0)) * 365)) or default_horizon_days
        out.append({"symbol": sym, "price": float(px), "horizon_days": hd,
                    "source": "dossier", "features": {"conviction": d.get("conviction")}})
    return out


# ------- Persistence -------

def save_ledger(path: str, entries: Iterable[GhostEntry]) -> None:
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump([asdict(e) for e in entries], f, indent=2)
    os.replace(tmp, path)


def load_ledger(path: str) -> list[GhostEntry]:
    try:
        with open(path) as f:
            raw = json.load(f)
    except (FileNotFoundError, ValueError):
        return []
    known = {fld.name for fld in fields(GhostEntry)}
    return [GhostEntry(**{k: v for k, v in row.items() if k in known}) for row in raw]
