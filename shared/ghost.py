"""Shared Ghost engine — a paper-only, unconstrained-breadth learning shadow.

A "ghost" runs a god's brain but places no orders and touches no real sleeve. It
opens a paper position for every candidate it can price — no concentration, no
caps, no min-ticket — marks the book to market over time, and grades each
position's forward return at its horizon. The point is DATA, not returns: enough
graded outcomes to measure whether the signals actually predict returns.

This module is god-agnostic. Each god supplies a thin adapter that turns its own
candidates (screen rows, events, …) into the generic `{symbol, price, source,
horizon_days, features}` shape, and composes a report from the analysis helpers
here. Keeping the engine in one place is deliberate: copying it per god is the
duplication trap that once put the same bug in two gods at once.
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
    source: str               # which god/adapter opened it ("screen", "event", …)
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
    skip_open: bool = False,
) -> list[GhostEntry]:
    """Build a paper entry for every priced candidate. No sizing, no caps.

    A candidate is {symbol, price, source?, horizon_days?, features?}. Names with
    no symbol or a non-positive price are skipped. Same-day re-opens of the same
    (symbol, source) are always de-duped.

    `skip_open=True` additionally skips any candidate that already has an
    *ungraded* (still-open) entry, regardless of date. Use it for a recurring run
    over a static candidate source (e.g. a weekly cron re-reading the quarterly
    screen) so the same names aren't re-opened every run. Leave it False when you
    want repeated entries over time as independent samples.
    """
    existing = list(existing)
    seen = {(e.symbol, e.source, e.entry_date) for e in existing}
    open_keys = {(e.symbol, e.source) for e in existing if not e.graded} if skip_open else set()
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
        if skip_open and (sym, source) in open_keys:
            continue
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


# ------- Mark-to-market: track the paper book over time -------

def mark_to_market(
    entries: Iterable[GhostEntry],
    price_lookup: PriceLookup,
    *,
    notional_per_position: float = 100.0,
) -> dict:
    """Value the whole paper book at current prices — a live portfolio snapshot.

    Equal-notional: every entry is `notional_per_position` of paper dollars bought
    at its entry price. Open positions are marked at the live quote; closed
    (graded) ones at their exit price. An open name that can't be priced right now
    is held flat (marked at entry) — grading resolves it later.
    """
    total_cost = 0.0
    market_value = 0.0
    n_open = n_closed = 0
    for e in entries:
        if e.entry_price <= 0:
            continue
        total_cost += notional_per_position
        if e.graded:
            mark = e.exit_price
            n_closed += 1
        else:
            px = price_lookup(e.symbol)
            mark = float(px) if (px is not None and px > 0) else e.entry_price
            n_open += 1
        market_value += notional_per_position * (mark / e.entry_price)
    total_return = (market_value / total_cost - 1.0) if total_cost > 0 else 0.0
    return {
        "equity": market_value,
        "cost_basis": total_cost,
        "total_return": total_return,
        "n_open": n_open,
        "n_closed": n_closed,
        "n": n_open + n_closed,
    }


def append_equity_point(
    curve: list[dict], date: str, snapshot: dict, *, benchmark: Optional[dict] = None,
) -> list[dict]:
    """Append a dated equity point to the curve (replacing any same-date point)."""
    point = {
        "date": date,
        "equity": round(snapshot.get("equity", 0.0), 2),
        "total_return": snapshot.get("total_return", 0.0),
        "n": snapshot.get("n", 0),
    }
    if benchmark:
        point["benchmark"] = dict(benchmark)
    out = [p for p in curve if p.get("date") != date]
    out.append(point)
    out.sort(key=lambda p: p.get("date", ""))
    return out


# ------- Analysis building blocks (gods compose their own reports) -------

def _mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def graded_only(entries: Iterable[GhostEntry]) -> list[GhostEntry]:
    return [e for e in entries if e.graded]


def overall_stats(graded: list[GhostEntry]) -> dict:
    rets = [e.graded_return for e in graded]
    n = len(rets)
    return {
        "n": n,
        "mean_return": (sum(rets) / n) if n else None,
        "hit_rate": (sum(1 for r in rets if r > 0) / n) if n else None,
    }


def boolean_lift(graded: list[GhostEntry]) -> dict:
    """Per boolean feature: mean return when it fired (True) vs explicit False.

    Entries missing the key are excluded so they can't pollute the lift.
    """
    flags = sorted({k for e in graded for k, v in e.features.items() if isinstance(v, bool)})
    out: dict[str, dict] = {}
    for f in flags:
        on = [e.graded_return for e in graded if e.features.get(f) is True]
        off = [e.graded_return for e in graded if e.features.get(f) is False]
        m_on, m_off = _mean(on), _mean(off)
        out[f] = {
            "n_on": len(on), "mean_on": m_on,
            "n_off": len(off), "mean_off": m_off,
            "lift": (m_on - m_off) if (m_on is not None and m_off is not None) else None,
        }
    return out


def group_stats(graded: list[GhostEntry], feature: str) -> dict:
    """Mean return grouped by a categorical feature (e.g. event_class)."""
    groups: dict[str, list[float]] = {}
    for e in graded:
        key = e.features.get(feature)
        if key is None:
            continue
        groups.setdefault(str(key), []).append(e.graded_return)
    return {k: {"n": len(v), "mean": _mean(v)} for k, v in sorted(groups.items())}


def tier_stats(
    graded: list[GhostEntry], feature: str, tier_fn: Callable[[float], str], order: tuple,
) -> dict:
    """Bucket a numeric feature into tiers and test monotonicity (high>=…>=low)."""
    tiers: dict[str, list[float]] = {t: [] for t in order}
    for e in graded:
        val = e.features.get(feature)
        if val is None:
            continue
        t = tier_fn(float(val))
        if t in tiers:
            tiers[t].append(e.graded_return)
    means = {t: _mean(v) for t, v in tiers.items()}
    present = [t for t in order if tiers[t]]
    monotonic = len(present) >= 2 and all(
        means[present[i]] >= means[present[i + 1]] for i in range(len(present) - 1)
    )
    return {"tiers": {t: {"n": len(tiers[t]), "mean": means[t]} for t in order}, "monotonic": monotonic}


def numeric_tercile_stats(graded: list[GhostEntry], feature: str) -> dict:
    """Split graded entries into terciles by a numeric feature; mean return each.

    Distribution-relative (no arbitrary cutoffs) — the right test for "does this
    numeric signal predict returns?". `monotonic` means high >= mid >= low.
    """
    vals = [
        (e.features.get(feature), e.graded_return) for e in graded
        if isinstance(e.features.get(feature), (int, float))
        and not isinstance(e.features.get(feature), bool)
    ]
    n = len(vals)
    if n < 3:
        return {"n": n, "terciles": {}, "monotonic": False}
    vals.sort(key=lambda vr: vr[0])
    k = n // 3
    low = [r for _, r in vals[:k]]
    high = [r for _, r in vals[n - k:]]
    mid = [r for _, r in vals[k:n - k]]
    means = {"low": _mean(low), "mid": _mean(mid), "high": _mean(high)}
    present = [t for t in ("high", "mid", "low") if means[t] is not None]
    monotonic = len(present) >= 2 and all(
        means[present[i]] >= means[present[i + 1]] for i in range(len(present) - 1)
    )
    return {
        "n": n,
        "terciles": {t: {"n": len(g), "mean": means[t]} for t, g in
                     (("high", high), ("mid", mid), ("low", low))},
        "monotonic": monotonic,
    }


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
