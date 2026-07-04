"""The Gauntlet — point-in-time strategy-factory backtest engine.

Backlog #9 (operator green-lit 2026-07-04): a decade+ daily-bar
simulation across the full Sharadar panel, running a pre-committed grid
of strategy variants, deflated-Sharpe corrected, holdout-gated. Build
order: (a) engine + SEP bulk pipeline [THIS MODULE], (b) factory prereg
(full grid enumerated, splits frozen) committed BEFORE any run, (c)
in-sample screen, (d) holdout pass for survivors only, (e) forward
tests. This module is infrastructure only — it runs no hypothesis, logs
no backtest, and touches no `shared.lab` registry; the grid itself is
phase (b)'s job.

Two things discovered building this that change (b)'s scope — status
in docs/lab_gauntlet_engine_status_2026-07-04.md:

1. **Storage.** The full Sharadar panel (~7,000 tickers pricing on any
   given day x ~2,500 trading days/decade) is ~17M OHLCV rows just for
   SEP — too large for a single JSON cache file (the house convention,
   built for hundreds of names). `shared.sharadar` DOES support true
   bulk pulls (a date range with no ticker filter returns the full
   cross-section, e.g. 6,835 rows for one day in one call — see
   `fetch_sep_bulk_range`), so the fetch side scales; what doesn't
   scale is dumping the result into `cache/shared_bars.json` the way
   `shared.historicals` does for per-symbol studies. The engine here
   therefore takes bars as an in-memory `bars_by_symbol` argument
   scoped to whatever candidate set phase (b) actually needs, rather
   than assuming a full-panel cache exists.
2. **Market cap — RESOLVED 2026-07-04 (same day).** SHARADAR/DAILY
   initially served only its free sample (XOM 2018) — the SEP-only
   subscription didn't entitle it. The operator bought the fundamentals
   upgrade the same day; DAILY now serves full cross-sections (~5,500-
   5,600 names/day, one page), history from late 1998, delisted names
   through their final trading day (verified SIVBQ, BBBYQ), marketcap
   in USD millions. `shared.sharadar.fetch_daily_bulk_range` is the
   sanctioned pull; feed its rows straight to `pit_snapshot`/
   `build_snapshots` with value_field="marketcap".
   `dollar_volume_pit_universe` below predates the upgrade and is
   SUPERSEDED for new work — kept because dollar-volume remains a
   legitimate LIQUIDITY screen to layer on top of a size universe, and
   because a committed prereg citing it stays honest. Backlog #4
   (Delphi PIT) is unblocked by the same purchase.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

EULER_MASCHERONI = 0.5772156649015329


# ---------------------------------------------------------------------------
# Cost model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CostModel:
    """Linear cost model: commission + slippage as bps of notional traded.

    Robinhood itself is commission-free, but a strategy-factory grid at
    house scale must not implicitly assume free, frictionless fills —
    slippage_bps is the load-bearing term for the thin small/mid-cap
    names this house actually trades. Defaults are a conservative
    placeholder; phase (b)'s prereg should set real numbers per
    liquidity bucket rather than trust these blindly.
    """
    commission_bps: float = 0.0
    slippage_bps: float = 10.0
    min_ticket: float = 25.0

    def total_cost(self, notional: float) -> float:
        if notional <= 0:
            return 0.0
        return notional * (self.commission_bps + self.slippage_bps) / 10_000.0


# ---------------------------------------------------------------------------
# Point-in-time universe construction
# ---------------------------------------------------------------------------

def pit_snapshot(
    rows: list[dict],
    snapshot_date: str,
    *,
    value_field: str = "marketcap",
    floor: Optional[float] = None,
    ceiling: Optional[float] = None,
) -> list[str]:
    """Tickers eligible at `snapshot_date`, using ONLY rows dated exactly
    that day — the no-lookahead guarantee is structural, not a filter
    someone can forget: a row from any other date is never consulted.

    `rows` is any list of {"date", "ticker", value_field} dicts — bulk
    SHARADAR/DAILY rows if that table is ever entitled, or a proxy
    table (e.g. dollar-volume rows from `dollar_volume_pit_universe`).
    """
    day = str(snapshot_date)[:10]
    out = []
    for r in rows:
        if str(r.get("date", ""))[:10] != day:
            continue
        v = r.get(value_field)
        if v is None:
            continue
        v = float(v)
        if floor is not None and v < floor:
            continue
        if ceiling is not None and v > ceiling:
            continue
        out.append(str(r["ticker"]).upper())
    return sorted(set(out))


def build_snapshots(
    rows: list[dict],
    snapshot_dates: list[str],
    *,
    value_field: str = "marketcap",
    floor: Optional[float] = None,
    ceiling: Optional[float] = None,
) -> dict[str, list[str]]:
    """{date: [tickers]} for each requested snapshot date.

    Raises if any requested date yields zero names — a silently empty
    snapshot is how a survivorship/coverage hole hides (same discipline
    as shared.historicals.ingest_raw's empty-ingest guard).
    """
    out: dict[str, list[str]] = {}
    empty = []
    for d in snapshot_dates:
        names = pit_snapshot(rows, d, value_field=value_field, floor=floor,
                              ceiling=ceiling)
        if not names:
            empty.append(d)
        out[str(d)[:10]] = names
    if empty:
        raise ValueError(
            f"snapshot(s) with zero eligible names: {empty} — check the "
            "source table is actually entitled/populated for these dates "
            "before trusting any other snapshot in this batch"
        )
    return out


def dollar_volume_pit_universe(
    sep_rows: list[dict],
    snapshot_dates: list[str],
    *,
    floor: Optional[float] = None,
    ceiling: Optional[float] = None,
) -> dict[str, list[str]]:
    """Dollar-volume (price x volume) universe from bulk SEP rows.

    Built as an interim market-cap proxy while SHARADAR/DAILY was
    unentitled; SUPERSEDED for size universes since the 2026-07-04
    fundamentals upgrade (use `fetch_daily_bulk_range` rows with
    `pit_snapshot(value_field="marketcap")`). Still legitimate as a
    LIQUIDITY screen layered on top of a size universe — that is why it
    stays. `sep_rows` are raw SEP datatable rows (ticker, date, close,
    volume, ...) as returned by `shared.sharadar.fetch_sep_bulk_range`,
    NOT canonicalized bars.
    """
    dv_rows = []
    for r in sep_rows:
        close = r.get("close")
        vol = r.get("volume")
        if close is None or vol is None:
            continue
        dv_rows.append({
            "date": str(r["date"])[:10],
            "ticker": str(r["ticker"]).upper(),
            "dollar_volume": float(close) * float(vol),
        })
    return build_snapshots(dv_rows, snapshot_dates, value_field="dollar_volume",
                            floor=floor, ceiling=ceiling)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

SelectFn = Callable[[str, list[str], dict[str, list[dict]]], dict[str, float]]


# ---------------------------------------------------------------------------
# Point-in-time event feed (insider clusters, earnings, spinoffs, ...)
# ---------------------------------------------------------------------------

class PITEventFeed:
    """Event table with the same structural no-lookahead guarantee
    `simulate` gives bars.

    Event-driven strategy families (insider clusters, PEAD, spinoffs,
    lockups) join their signal in through the spec's closure — which
    makes event data a lookahead surface the bar-trimming guarantee
    does not cover. This class closes it: rows must be keyed by the
    date the information became PUBLIC (the filing/announcement date,
    default field `public_date`), never the economic event date — an
    insider-cluster row keyed on the transaction date leaks the 2–10
    day filing lag into every decision. The constructor refuses rows
    missing the date field so the guarantee is structural, and select()
    functions should only ever touch events via `upto(as_of)` /
    `on(day)` / `by_symbol(as_of)`.
    """

    def __init__(self, rows: list[dict], *, date_field: str = "public_date"):
        self.date_field = date_field
        for i, r in enumerate(rows):
            if not r.get(date_field):
                raise ValueError(
                    f"event row {i} missing '{date_field}' — every row must be "
                    "keyed by the date the information became public "
                    "(filing/announcement date, not the economic event date)")
        self._rows = sorted(rows, key=lambda r: str(r[date_field])[:10])

    def upto(self, as_of: str) -> list[dict]:
        """All events public on or before `as_of` — never a future row."""
        cutoff = str(as_of)[:10]
        return [r for r in self._rows
                if str(r[self.date_field])[:10] <= cutoff]

    def on(self, day: str) -> list[dict]:
        """Events that became public exactly on `day`."""
        d = str(day)[:10]
        return [r for r in self._rows if str(r[self.date_field])[:10] == d]

    def by_symbol(self, as_of: str, *, symbol_field: str = "symbol") -> dict:
        """`upto(as_of)` grouped by symbol, for O(1) lookups in select()."""
        out: dict = {}
        for r in self.upto(as_of):
            out.setdefault(r.get(symbol_field), []).append(r)
        return out

    def __len__(self) -> int:
        return len(self._rows)


@dataclass
class StrategySpec:
    """A grid entry: a name plus a rule that maps
    (as_of_date, universe, bars_by_symbol_trimmed_to_as_of) -> target
    weights ({symbol: fraction_of_equity}, need not sum to 1.0 — the
    remainder sits in cash).
    """
    name: str
    select: SelectFn
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExitRules:
    """Daily position-level exit rules, evaluated between rebalances.

    This is what the 90-cell gauntlet_v1 grid deliberately lacked
    (rank-and-hold only) and what every live god actually runs: Delphi's
    20-day-MA trailing exit, Achilles' -8% hard stop + 5-day time stop,
    Midas's -10% stop + Friday time stop. Added 2026-07-04 so bespoke
    rulesets can be simulated as implemented, not as strawmen.

    Trigger discipline — triggers evaluate on RAW split-adjusted prices
    (`close`/`open`/`low`/`high`), because that is what a live god
    computes stops and MAs on at the broker; book fills then convert to
    the symbol's marking series (total-return ratio for that day) so
    the cash accounting stays dividend-correct. Intraday rules
    (stop_loss, trailing_stop, profit_target) use the day's low/high
    when the bar carries them — gap-throughs fill at the open, ordinary
    touches at the trigger level — and degrade to close-crossing checks
    on close-only bars. Close rules (ma, time) fill at the close.

    Evaluation order per held name per day (first hit wins):
    stop_loss -> trailing_stop -> profit_target -> ma -> time. The
    trailing stop compares against the PRIOR peak close (today's move
    can trigger it, not ratchet it first). Exits run BEFORE any same-day
    rebalance, and an exited name cannot be re-bought the same day;
    `cooldown_days` extends that block for N further trading days.

    All fields optional; None disables a rule. On adds to an existing
    position, entry price averages in share-weighted; the time-stop
    clock does NOT reset (first entry starts it).
    """
    ma_period: Optional[int] = None           # exit when close < SMA(N closes)
    stop_loss_pct: Optional[float] = None     # 0.08 = exit -8% below entry
    trailing_stop_pct: Optional[float] = None  # 0.10 = exit -10% below peak close
    time_stop_days: Optional[int] = None      # exit at close after N trading days
    profit_target_pct: Optional[float] = None  # 0.20 = exit +20% above entry
    cooldown_days: int = 0                    # extra re-entry block after any exit


def _trading_days(bars_by_symbol: dict[str, list[dict]],
                   start: Optional[str], end: Optional[str]) -> list[str]:
    days: set[str] = set()
    for bars in bars_by_symbol.values():
        for b in bars:
            d = b["date"]
            if start and d < start:
                continue
            if end and d > end:
                continue
            days.add(d)
    return sorted(days)


def _trim(bars_by_symbol: dict[str, list[dict]],
          as_of: str) -> dict[str, list[dict]]:
    return {s: [b for b in bars if b["date"] <= as_of]
            for s, bars in bars_by_symbol.items()}


class _LazyTrim:
    """Read-only, lazily-trimmed view of bars_by_symbol as of a date.

    Behaviorally identical to `_trim`'s dict for select() consumers,
    but O(log n) bisect + one slice per symbol ACCESSED instead of
    copying the whole panel per rebalance — the difference between
    minutes and hours on a 27-year weekly simulation. Bars lists are
    assumed date-sorted (the engine's standing input contract).
    """

    def __init__(self, bars_by_symbol: dict[str, list[dict]],
                 dates_by_symbol: dict[str, list[str]], as_of: str):
        self._bars = bars_by_symbol
        self._dates = dates_by_symbol
        self._as_of = as_of

    def _cut(self, sym: str) -> int:
        import bisect
        return bisect.bisect_right(self._dates[sym], self._as_of)

    def __getitem__(self, sym: str) -> list[dict]:
        return self._bars[sym][:self._cut(sym)]

    def tail(self, sym: str, n: int) -> list[dict]:
        """Last n bars as of the view date, without copying the full
        history — the fast path for lookback signals (momentum, MAs)."""
        cut = self._cut(sym)
        return self._bars[sym][max(0, cut - n):cut]

    def get(self, sym: str, default=None):
        return self[sym] if sym in self._bars else default

    def __contains__(self, sym: str) -> bool:
        return sym in self._bars

    def __iter__(self):
        return iter(self._bars)

    def __len__(self) -> int:
        return len(self._bars)

    def keys(self):
        return self._bars.keys()

    def items(self):
        return ((s, self[s]) for s in self._bars)


def _price_field_by_symbol(bars_by_symbol: dict[str, list[dict]]) -> dict[str, str]:
    """Pick the marking price per symbol: total return when complete.

    `close` is split-adjusted but dividend-EXCLUSIVE, so an equity curve
    marked on it silently drops every dividend — ~2%/yr on the broad
    market, and differentially worse for value/quality/dividend
    families, which corrupts cross-family ranking (found 2026-07-04).
    `close_total_return` (Sharadar closeadj) fixes that, but mixing the
    two fields within one symbol would inject a fake jump at every
    coverage gap — so the total-return series is used only when EVERY
    bar of that symbol carries it; otherwise the whole symbol falls
    back to `close` and is disclosed in the result's
    `price_return_only_symbols`.
    """
    fields: dict[str, str] = {}
    for s, bars in bars_by_symbol.items():
        if bars and all(b.get("close_total_return") is not None for b in bars):
            fields[s] = "close_total_return"
        else:
            fields[s] = "close"
    return fields


def simulate(
    spec: StrategySpec,
    snapshots: dict[str, list[str]],
    bars_by_symbol: dict[str, list[dict]],
    *,
    initial_cash: float = 1000.0,
    cost: CostModel = CostModel(),
    start: Optional[str] = None,
    end: Optional[str] = None,
    signal_lag: int = 0,
    exits: Optional[ExitRules] = None,
    delist_exit_haircut: Optional[float] = None,
    rebalance_band: float = 0.0,
    sell_cooldown_days: int = 0,
) -> dict:
    """Run one strategy through one point-in-time universe series.

    Rebalances on every date present in `snapshots`; marks equity daily
    on every trading day the underlying bars cover. A symbol missing a
    bar on a given day carries forward its last known price (documented
    approximation — see module docstring on delisted-name handling;
    Sharadar SEP bars already run through a name's true final trading
    day, so gaps here are trading halts, not survivorship holes).

    Marks and fills on `close_total_return` (split+dividend adjusted)
    for every symbol whose bars carry it completely, so dividends
    compound instead of vanishing; symbols without full total-return
    coverage fall back to split-adjusted `close` and are disclosed in
    the result's `price_return_only_symbols` — a results doc citing a
    run with a non-empty list must say so. Note the `trimmed` bars a
    spec's select() receives are untouched: signals computed on `close`
    are legitimate; only the book's marking is total-return.

    `signal_lag` (trading days) trims the bars the selection rule sees
    to `signal_lag` days BEFORE the execution day, while trades still
    fill at the execution day's close. With the default 0 the rule sees
    the execution day's own close — same-day signal-and-trade, a one-
    day look-ahead for fast signals. gauntlet_v1's prereg (section 4)
    mandates signal_lag=1: signals through close of t, execution at
    close of t+1. Lag counts positions in this simulation's own
    trading-day index; a rebalance earlier than `signal_lag` days into
    the window raises (no silent no-lag fallback).

    `exits` (see ExitRules) adds daily position-level exit evaluation —
    MA breaks, hard/trailing stops, time stops, profit targets,
    re-entry cooldowns. Exit sells carry a `reason` field in the trades
    list ("stop_loss", "ma_exit", ...); rebalance trades carry
    reason="rebalance".

    `delist_exit_haircut` addresses the documented optimistic bias
    around delistings (a dead name's stale final close was sellable at
    the next rebalance): when set, any position still held on its
    symbol's FINAL bar date in the panel is force-sold that day at
    final close x (1 - haircut), reason "delisting_exit". 0.0 = exit at
    the final print; 0.5 = assume half is lost; None = legacy stale-
    close behavior. Use as a robustness rerun, not a default — Sharadar
    final bars are real last trading days, and many "final bars" are
    simply the panel window ending.

    `rebalance_band` (fraction, e.g. 0.20) is drift-band damping at
    rebalances, matching delphi/backtest.py's semantics exactly: a held
    name is trimmed only when its value exceeds target*(1+band) and
    topped up only when below target*(1-band); FULL exits (target 0)
    always fire. `sell_cooldown_days` blocks re-BUYING a name for N
    trading days after any full rebalance exit (rotation sells), the
    live cooldown-on-any-sell rule; ExitRules.cooldown_days continues
    to govern exits triggered by exit rules.
    """
    if signal_lag < 0:
        raise ValueError(f"signal_lag must be >= 0, got {signal_lag}")
    all_days = _trading_days(bars_by_symbol, start, end)
    if not all_days:
        raise ValueError("no trading days in bars_by_symbol for the given window")
    day_index = {d: i for i, d in enumerate(all_days)}
    rebalance_dates = {d for d in snapshots if (not start or d >= start)
                        and (not end or d <= end)}
    price_field = _price_field_by_symbol(bars_by_symbol)
    bar_lookup = {s: {b["date"]: b for b in bars}
                  for s, bars in bars_by_symbol.items()}
    dates_by_symbol = {s: [b["date"] for b in bars]
                       for s, bars in bars_by_symbol.items()}
    final_bar_date = {s: bars[-1]["date"] if bars else None
                      for s, bars in bars_by_symbol.items()}

    cash = initial_cash
    positions: dict[str, float] = {}
    last_price: dict[str, float] = {}
    raw_last: dict[str, float] = {}          # last RAW close per symbol
    closes_hist: dict[str, list[float]] = {}  # running raw closes (for MAs)
    pos_meta: dict[str, dict] = {}           # entry_raw / entry_idx / peak_raw
    cooldown_until: dict[str, int] = {}      # day index through which buys block
    curve: list[dict] = []
    trades: list[dict] = []

    def _book_px(sym: str, raw_px: float, bar: dict) -> float:
        """Convert a raw trigger price into the symbol's marking series."""
        if price_field[sym] == "close_total_return" and bar.get("close"):
            return raw_px * bar["close_total_return"] / bar["close"]
        return raw_px

    def _sell_all(sym: str, book_px: float, day_: str, reason: str) -> None:
        nonlocal cash
        shares = positions.pop(sym)
        proceeds = shares * book_px
        cost_amt = cost.total_cost(proceeds)
        cash += proceeds - cost_amt
        trades.append({"date": day_, "symbol": sym, "side": "sell",
                        "shares": shares, "price": book_px,
                        "cost": cost_amt, "reason": reason})
        pos_meta.pop(sym, None)

    for day in all_days:
        for s, bars in bars_by_symbol.items():
            b = bar_lookup[s].get(day)
            if b is not None:
                last_price[s] = b[price_field[s]]
                raw_last[s] = b["close"]
                closes_hist.setdefault(s, []).append(b["close"])

        # -- daily exit rules (before any same-day rebalance) ------------
        if exits is not None and positions:
            for s in list(positions):
                b = bar_lookup[s].get(day)
                if b is None:
                    continue  # halted today — can't trade what doesn't print
                meta = pos_meta.get(s)
                if meta is None:
                    continue
                raw_close = b["close"]
                lo, hi, op = b.get("low"), b.get("high"), b.get("open")
                fill_raw: Optional[float] = None
                reason: Optional[str] = None

                def _stop_fill(level: float) -> Optional[float]:
                    # Gap through the level -> the open is the best you get;
                    # ordinary touch -> the level; close-only bars degrade
                    # to a close-crossing check.
                    if op is not None and op <= level:
                        return op
                    if lo is not None:
                        return level if lo <= level else None
                    return raw_close if raw_close <= level else None

                if exits.stop_loss_pct is not None:
                    fill_raw = _stop_fill(
                        meta["entry_raw"] * (1 - exits.stop_loss_pct))
                    reason = "stop_loss" if fill_raw is not None else None
                if fill_raw is None and exits.trailing_stop_pct is not None:
                    fill_raw = _stop_fill(
                        meta["peak_raw"] * (1 - exits.trailing_stop_pct))
                    reason = "trailing_stop" if fill_raw is not None else None
                if fill_raw is None and exits.profit_target_pct is not None:
                    level = meta["entry_raw"] * (1 + exits.profit_target_pct)
                    if op is not None and op >= level:
                        fill_raw, reason = op, "profit_target"
                    elif hi is not None and hi >= level:
                        fill_raw, reason = level, "profit_target"
                    elif hi is None and op is None and raw_close >= level:
                        fill_raw, reason = raw_close, "profit_target"
                if fill_raw is None and exits.ma_period is not None:
                    hist = closes_hist.get(s, [])
                    if len(hist) >= exits.ma_period:
                        sma = sum(hist[-exits.ma_period:]) / exits.ma_period
                        if raw_close < sma:
                            fill_raw, reason = raw_close, "ma_exit"
                if fill_raw is None and exits.time_stop_days is not None:
                    if day_index[day] - meta["entry_idx"] >= exits.time_stop_days:
                        fill_raw, reason = raw_close, "time_stop"

                if fill_raw is not None:
                    _sell_all(s, _book_px(s, fill_raw, b), day, reason)
                    cooldown_until[s] = day_index[day] + exits.cooldown_days
                else:
                    meta["peak_raw"] = max(meta["peak_raw"], raw_close)

        # -- forced delisting exit (robustness mode) ---------------------
        if delist_exit_haircut is not None:
            for s in list(positions):
                if final_bar_date.get(s) == day:
                    b = bar_lookup[s][day]
                    fill = b["close"] * (1 - delist_exit_haircut)
                    _sell_all(s, _book_px(s, fill, b), day, "delisting_exit")
                    cooldown_until[s] = day_index[day]  # never re-buyable anyway

        if day in rebalance_dates:
            universe = snapshots[day]
            if signal_lag:
                i = day_index[day] - signal_lag
                if i < 0:
                    raise ValueError(
                        f"{spec.name} on {day}: rebalance falls {signal_lag} "
                        "trading day(s) from the window start — no lagged "
                        "signal date exists; extend the bar window or drop "
                        "this rebalance date")
                signal_day = all_days[i]
            else:
                signal_day = day
            trimmed = _LazyTrim(bars_by_symbol, dates_by_symbol, signal_day)
            equity_now = cash + sum(
                positions[s] * last_price.get(s, 0.0) for s in positions)
            weights = spec.select(day, universe, trimmed)
            total_w = sum(weights.values())
            if total_w > 1.0 + 1e-6:
                raise ValueError(
                    f"{spec.name} on {day}: weights sum to {total_w:.4f} > 1.0")
            target_value = {s: w * equity_now for s, w in weights.items()}

            all_syms = set(positions) | set(target_value)
            # Sells first — free cash before any buy needs it.
            for s in all_syms:
                tgt = target_value.get(s, 0.0)
                px = last_price.get(s)
                cur_shares = positions.get(s, 0.0)
                if px is None or px <= 0 or cur_shares <= 0:
                    continue
                delta = tgt - cur_shares * px
                if delta >= -cost.min_ticket:
                    continue
                if (rebalance_band > 0.0 and tgt > 0.0
                        and cur_shares * px <= tgt * (1.0 + rebalance_band)):
                    continue  # inside the drift band — let it ride
                sell_notional = min(-delta, cur_shares * px)
                shares_sold = sell_notional / px
                proceeds = shares_sold * px
                cost_amt = cost.total_cost(proceeds)
                cash += proceeds - cost_amt
                remaining = cur_shares - shares_sold
                if remaining <= 1e-9:
                    positions.pop(s, None)
                else:
                    positions[s] = remaining
                trades.append({"date": day, "symbol": s, "side": "sell",
                                "shares": shares_sold, "price": px,
                                "cost": cost_amt, "reason": "rebalance"})
                if s not in positions:
                    pos_meta.pop(s, None)
                    if sell_cooldown_days > 0:
                        cooldown_until[s] = max(
                            cooldown_until.get(s, -1),
                            day_index[day] + sell_cooldown_days)
            # Then buys, bounded by cash actually on hand. When cash
            # (after costs) can't cover every buy, all buys scale
            # pro-rata — a sequential fill would silently short-change
            # whichever symbol sorts last.
            buy_deltas: dict[str, float] = {}
            for s in all_syms:
                if day_index[day] <= cooldown_until.get(s, -1):
                    continue  # exited today or still cooling down
                tgt = target_value.get(s, 0.0)
                px = last_price.get(s)
                cur_shares = positions.get(s, 0.0)
                if px is None or px <= 0:
                    continue
                delta = tgt - cur_shares * px
                if delta < cost.min_ticket:
                    continue
                if (rebalance_band > 0.0
                        and cur_shares * px >= tgt * (1.0 - rebalance_band)):
                    continue  # inside the drift band — no top-up churn
                buy_deltas[s] = delta
            denom = 1 + (cost.commission_bps + cost.slippage_bps) / 10_000.0
            total_buys = sum(buy_deltas.values())
            scale = min(1.0, (cash / denom) / total_buys) if total_buys > 0 else 0.0
            for s, delta in buy_deltas.items():
                px = last_price[s]
                spend = delta * scale
                if spend < cost.min_ticket:
                    continue
                shares_bought = spend / px
                cost_amt = cost.total_cost(spend)
                cash -= spend + cost_amt
                prior_shares = positions.get(s, 0.0)
                positions[s] = prior_shares + shares_bought
                raw_px = raw_last.get(s, px)
                meta = pos_meta.get(s)
                if meta is None or prior_shares <= 0:
                    pos_meta[s] = {"entry_raw": raw_px,
                                   "entry_idx": day_index[day],
                                   "peak_raw": raw_px}
                else:  # share-weighted average-in; time clock does not reset
                    total = prior_shares + shares_bought
                    meta["entry_raw"] = (meta["entry_raw"] * prior_shares
                                          + raw_px * shares_bought) / total
                    meta["peak_raw"] = max(meta["peak_raw"], raw_px)
                trades.append({"date": day, "symbol": s, "side": "buy",
                                "shares": shares_bought, "price": px,
                                "cost": cost_amt, "reason": "rebalance"})

        equity = cash + sum(positions[s] * last_price.get(s, 0.0)
                             for s in positions)
        curve.append({"date": day, "equity": equity,
                       "n_positions": len(positions)})

    return {"curve": curve, "trades": trades, "stats": summarize(curve),
            "price_return_only_symbols": sorted(
                s for s, f in price_field.items() if f == "close")}


# ---------------------------------------------------------------------------
# Performance stats
# ---------------------------------------------------------------------------

def _moments(xs: list[float]) -> tuple[float, float, float, float]:
    n = len(xs)
    if n == 0:
        return 0.0, 0.0, 0.0, 3.0
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / n
    std = math.sqrt(var)
    if std == 0:
        return mean, 0.0, 0.0, 3.0
    skew = (sum((x - mean) ** 3 for x in xs) / n) / std ** 3
    kurt = (sum((x - mean) ** 4 for x in xs) / n) / std ** 4
    return mean, std, skew, kurt


def summarize(curve: list[dict]) -> dict:
    """Annualized (252 trading-day) stats off a daily equity curve."""
    equities = [c["equity"] for c in curve]
    if len(equities) < 2 or equities[0] <= 0:
        return {"n_obs": 0, "total_return": 0.0, "cagr": 0.0, "sharpe": 0.0,
                "sortino": 0.0, "max_drawdown": 0.0, "win_rate": 0.0,
                "skew": 0.0, "kurtosis": 3.0}

    rets = [equities[i] / equities[i - 1] - 1.0 for i in range(1, len(equities))
            if equities[i - 1] > 0]
    n = len(rets)
    mean, std, skew, kurt = _moments(rets)
    sharpe = (mean / std) * math.sqrt(252) if std > 0 else 0.0

    downside = [r for r in rets if r < 0]
    _, dstd, _, _ = _moments(downside)
    sortino = (mean / dstd) * math.sqrt(252) if dstd > 0 else 0.0

    peak = equities[0]
    max_dd = 0.0
    for e in equities:
        peak = max(peak, e)
        if peak > 0:
            max_dd = min(max_dd, e / peak - 1.0)

    total_return = equities[-1] / equities[0] - 1.0
    years = n / 252.0
    cagr = ((equities[-1] / equities[0]) ** (1 / years) - 1.0) if years > 0 else 0.0
    win_rate = (sum(1 for r in rets if r > 0) / n) if n else 0.0

    return {"n_obs": n, "total_return": total_return, "cagr": cagr,
            "sharpe": sharpe, "sortino": sortino, "max_drawdown": max_dd,
            "win_rate": win_rate, "skew": skew, "kurtosis": kurt}


def summarize_by_period(curve: list[dict], boundaries: list[str]) -> dict:
    """Split one equity curve at boundary dates; summarize each segment.

    The per-regime disclosure every Gauntlet results doc must print: a
    full-panel Sharpe is an average over regimes a survivor may never
    see again, and the house has been burned by exactly this (the
    warm-vintage spinoff +41% that was −1% out of regime). Segments are
    [start, b1), [b1, b2), …, [bn, end]; each maps
    "<first-date>..<last-date>" → summarize(segment). Empty segments
    are omitted; a boundary set that leaves everything in one segment
    just returns the full-curve stats under one key.
    """
    cuts = sorted(str(b)[:10] for b in boundaries)
    segments: list[list[dict]] = [[] for _ in range(len(cuts) + 1)]
    for point in curve:
        d = str(point["date"])[:10]
        idx = sum(1 for c in cuts if d >= c)
        segments[idx].append(point)
    out: dict = {}
    for seg in segments:
        if not seg:
            continue
        label = f"{seg[0]['date']}..{seg[-1]['date']}"
        out[label] = summarize(seg)
    return out


def convexity_stats(trade_returns, *, benchmark_returns=None, tail_pct: float = 0.10) -> dict:
    """The RETURN-oriented objective (2026-07-04 pivot): score an event/
    situation strategy on CONVEXITY, not mean excess.

    Return-maximization on a small long-only, no-leverage book comes from a
    survivable FLOOR per bet and a large RIGHT TAIL — not from beating a
    benchmark by a thin average. The gauntlet's mean-excess bar is the wrong
    objective for that; this is the right one. The unit is the TRADE (one
    event -> one net return), e.g. 0.15 = +15%. Pass `benchmark_returns`
    (same length/order) to score excess-per-trade instead of raw.

    Key fields:
    - `floor`  : worst single trade — the survivability number (is the
                 per-bet downside bounded? a merger break vs a wipeout).
    - `payoff_ratio` : avg win / |avg loss| — asymmetry.
    - `right_tail_share` : fraction of total positive P&L from the top
                 `tail_pct` of trades — how much the result rides the tail
                 (high = convex/lottery-shaped; know it before sizing).
    - `expectancy` : mean net return per trade (the thing that compounds).
    """
    import statistics as _stats
    if benchmark_returns is not None:
        rs = [r - b for r, b in zip(trade_returns, benchmark_returns)]
    else:
        rs = list(trade_returns)
    n = len(rs)
    if n == 0:
        return {"n": 0}
    rs_sorted = sorted(rs)
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]

    def pct(p):
        i = min(len(rs_sorted) - 1, max(0, int(round(p * (len(rs_sorted) - 1)))))
        return rs_sorted[i]

    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    mean = sum(rs) / n
    k = max(1, int(round(tail_pct * n)))
    total_pos = sum(r for r in rs if r > 0)
    right_tail_share = (sum(r for r in rs_sorted[-k:] if r > 0) / total_pos
                        if total_pos > 0 else 0.0)
    payoff_ratio = (avg_win / abs(avg_loss)) if avg_loss < 0 else None
    return {
        "n": n,
        "expectancy": round(mean, 4),
        "median": round(_stats.median(rs), 4),
        "win_rate": round(len(wins) / n, 3),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "payoff_ratio": round(payoff_ratio, 2) if payoff_ratio is not None else None,
        "p95_upside": round(pct(0.95), 4),
        "max": round(rs_sorted[-1], 4),
        "p10_downside": round(pct(0.10), 4),
        "floor": round(rs_sorted[0], 4),
        "right_tail_share": round(right_tail_share, 3),
    }


def excess_stats(curve: list[dict], benchmark_curve: list[dict]) -> dict:
    """Benchmark-relative statistics from two daily equity curves.

    Aligns on common dates, then reports the numbers a benchmark-
    relative pass bar actually needs: annualized excess return (CAGR
    difference), beta and annualized alpha (daily OLS of strategy
    returns on benchmark returns), tracking error, information ratio,
    and up/down capture. gauntlet_v1's lesson made the bar benchmark-
    relative; this makes the comparison one call instead of ad-hoc
    arithmetic in every runner script.
    """
    eq = {str(c["date"])[:10]: c["equity"] for c in curve}
    bq = {str(c["date"])[:10]: c["equity"] for c in benchmark_curve}
    days = sorted(set(eq) & set(bq))
    if len(days) < 3:
        return {"n_obs": 0}
    rs, rb = [], []
    for i in range(1, len(days)):
        p0, p1 = eq[days[i - 1]], eq[days[i]]
        b0, b1 = bq[days[i - 1]], bq[days[i]]
        if p0 <= 0 or b0 <= 0:
            continue
        rs.append(p1 / p0 - 1.0)
        rb.append(b1 / b0 - 1.0)
    n = len(rs)
    if n < 2:
        return {"n_obs": n}
    mean_s = sum(rs) / n
    mean_b = sum(rb) / n
    var_b = sum((x - mean_b) ** 2 for x in rb) / n
    cov = sum((rs[i] - mean_s) * (rb[i] - mean_b) for i in range(n)) / n
    beta = cov / var_b if var_b > 0 else 0.0
    alpha_daily = mean_s - beta * mean_b
    diffs = [rs[i] - rb[i] for i in range(n)]
    mean_d, std_d, _, _ = _moments(diffs)
    years = n / 252.0
    cagr_s = (eq[days[-1]] / eq[days[0]]) ** (1 / years) - 1.0 if years > 0 else 0.0
    cagr_b = (bq[days[-1]] / bq[days[0]]) ** (1 / years) - 1.0 if years > 0 else 0.0
    up = [(rs[i], rb[i]) for i in range(n) if rb[i] > 0]
    down = [(rs[i], rb[i]) for i in range(n) if rb[i] < 0]
    up_cap = (sum(s for s, _ in up) / sum(b for _, b in up)) if up and sum(b for _, b in up) != 0 else 0.0
    down_cap = (sum(s for s, _ in down) / sum(b for _, b in down)) if down and sum(b for _, b in down) != 0 else 0.0
    return {
        "n_obs": n,
        "cagr": cagr_s, "benchmark_cagr": cagr_b,
        "excess_cagr": cagr_s - cagr_b,
        "beta": beta,
        "alpha_annual": alpha_daily * 252,
        "tracking_error": std_d * math.sqrt(252),
        "information_ratio": (mean_d / std_d) * math.sqrt(252) if std_d > 0 else 0.0,
        "up_capture": up_cap, "down_capture": down_cap,
    }


def trade_stats(trades: list[dict]) -> dict:
    """Round-trip statistics from a simulate() trades list (FIFO lots).

    Matches sells against buy lots per symbol first-in-first-out and
    reports: round-trip count, win rate, average win/loss %, profit
    factor, median holding period (calendar days), and a per-exit-
    reason breakdown — so an ExitRules run can answer 'did the stop
    save money or amputate winners?' directly, the same signal_lift
    question the ghosts ask live.
    """
    from datetime import date as _d

    def _days(a: str, b: str) -> int:
        y1, m1, d1 = map(int, a[:10].split("-"))
        y2, m2, d2 = map(int, b[:10].split("-"))
        return (_d(y2, m2, d2) - _d(y1, m1, d1)).days

    lots: dict[str, list[dict]] = {}
    round_trips: list[dict] = []
    for t in trades:
        sym = t["symbol"]
        if t["side"] == "buy":
            lots.setdefault(sym, []).append(
                {"shares": t["shares"], "price": t["price"], "date": t["date"]})
            continue
        remaining = t["shares"]
        while remaining > 1e-12 and lots.get(sym):
            lot = lots[sym][0]
            take = min(remaining, lot["shares"])
            ret = (t["price"] - lot["price"]) / lot["price"] if lot["price"] > 0 else 0.0
            round_trips.append({
                "symbol": sym, "return_pct": ret,
                "holding_days": _days(lot["date"], t["date"]),
                "reason": t.get("reason", "rebalance"),
                "notional": take * lot["price"],
            })
            lot["shares"] -= take
            remaining -= take
            if lot["shares"] <= 1e-12:
                lots[sym].pop(0)
    n = len(round_trips)
    if n == 0:
        return {"n_round_trips": 0}
    wins = [r for r in round_trips if r["return_pct"] > 0]
    losses = [r for r in round_trips if r["return_pct"] <= 0]
    gross_win = sum(r["return_pct"] * r["notional"] for r in wins)
    gross_loss = -sum(r["return_pct"] * r["notional"] for r in losses)
    hold = sorted(r["holding_days"] for r in round_trips)
    by_reason: dict[str, dict] = {}
    for r in round_trips:
        g = by_reason.setdefault(r["reason"], {"n": 0, "wins": 0, "sum_return": 0.0})
        g["n"] += 1
        g["wins"] += 1 if r["return_pct"] > 0 else 0
        g["sum_return"] += r["return_pct"]
    for g in by_reason.values():
        g["win_rate"] = g["wins"] / g["n"]
        g["mean_return"] = g["sum_return"] / g["n"]
    return {
        "n_round_trips": n,
        "win_rate": len(wins) / n,
        "avg_win_pct": sum(r["return_pct"] for r in wins) / len(wins) if wins else 0.0,
        "avg_loss_pct": sum(r["return_pct"] for r in losses) / len(losses) if losses else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss > 0 else math.inf,
        "median_holding_days": hold[n // 2],
        "by_exit_reason": by_reason,
    }


def turnover_stats(trades: list[dict], curve: list[dict]) -> dict:
    """Annual turnover and cost attribution from a simulate() result.

    turnover = annualized sell notional / average equity (single-
    sided); cost_drag_bps_yr = total costs paid / average equity /
    years, in bps. The number that decides whether a paper edge
    survives its own trading — the fee-engine check Proteus runs by
    hand, mechanized.
    """
    if not curve:
        return {"n_obs": 0}
    equities = [c["equity"] for c in curve]
    avg_eq = sum(equities) / len(equities)
    years = max(len(equities) - 1, 1) / 252.0
    sell_notional = sum(t["shares"] * t["price"] for t in trades
                        if t["side"] == "sell")
    buy_notional = sum(t["shares"] * t["price"] for t in trades
                       if t["side"] == "buy")
    total_costs = sum(t.get("cost", 0.0) for t in trades)
    return {
        "n_obs": len(equities),
        "avg_equity": avg_eq,
        "annual_turnover": (sell_notional / avg_eq / years) if avg_eq > 0 else 0.0,
        "buy_notional": buy_notional,
        "sell_notional": sell_notional,
        "total_costs": total_costs,
        "cost_drag_bps_yr": (total_costs / avg_eq / years * 10_000) if avg_eq > 0 else 0.0,
    }


def periodic_dates(days: list[str], cadence: str = "M",
                    anchor: str = "last") -> list[str]:
    """Rebalance calendar from a trading-day list: weekly or monthly.

    cadence "M" groups by calendar month, "W" by ISO week; anchor
    "last" takes each group's final trading day (signal at the close
    that ends the period), "first" its opening day. Feed the result to
    snapshot construction so a weekly-cadence god (Delphi) or monthly
    grid cell shares one canonical calendar-building path.
    """
    from datetime import date as _d
    if cadence not in ("M", "W"):
        raise ValueError(f"cadence must be 'M' or 'W', got {cadence!r}")
    if anchor not in ("first", "last"):
        raise ValueError(f"anchor must be 'first' or 'last', got {anchor!r}")
    groups: dict = {}
    for day in sorted(str(d)[:10] for d in days):
        if cadence == "M":
            key = day[:7]
        else:
            y, m, dd = map(int, day.split("-"))
            iso = _d(y, m, dd).isocalendar()
            key = (iso[0], iso[1])
        if anchor == "first":
            groups.setdefault(key, day)
        else:
            groups[key] = day
    return sorted(groups.values())


# ---------------------------------------------------------------------------
# Deflated Sharpe ratio (Bailey & Lopez de Prado, 2014) — the
# multiple-testing-corrected bar backlog #9 requires by name.
# ---------------------------------------------------------------------------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (Acklam's rational approximation,
    ~1.15e-9 max error) — no scipy/numpy in this environment.
    """
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low, p_high = 0.02425, 1 - 0.02425
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def expected_max_sharpe(n_trials: int, variance_of_sr: float = 1.0) -> float:
    """E[max SR] among `n_trials` independent strategies with SR~N(0,
    variance_of_sr) — the benchmark that turns a raw Sharpe into a
    multiple-testing-aware one. `n_trials` should be the grid size
    (or, house-wide, `lab["hypotheses_ever"]`), never a per-strategy
    count of 1.
    """
    if n_trials < 2:
        return 0.0
    z1 = (1 - EULER_MASCHERONI) * _norm_ppf(1 - 1.0 / n_trials)
    z2 = EULER_MASCHERONI * _norm_ppf(1 - 1.0 / (n_trials * math.e))
    return math.sqrt(variance_of_sr) * (z1 + z2)


def probabilistic_sharpe_ratio(
    sr_observed: float, sr_benchmark: float, n_obs: int, *,
    skew: float = 0.0, kurtosis: float = 3.0,
) -> float:
    """P(true SR > sr_benchmark) given the observed SR over n_obs
    returns, adjusted for skew/kurtosis (fat tails inflate a naive
    Sharpe more than a normal-returns assumption admits).
    """
    if n_obs < 2:
        raise ValueError("n_obs must be >= 2")
    denom = math.sqrt(max(1e-12,
                          1 - skew * sr_observed + (kurtosis - 1) / 4.0 * sr_observed ** 2))
    z = (sr_observed - sr_benchmark) * math.sqrt(n_obs - 1) / denom
    return _norm_cdf(z)


def deflated_sharpe_ratio(
    sr_observed: float, *, n_trials: int, n_obs: int,
    skew: float = 0.0, kurtosis: float = 3.0, variance_of_sr: float = 1.0,
) -> float:
    """DSR: probabilistic Sharpe ratio benchmarked against the expected
    max Sharpe of `n_trials` trials instead of zero. This is what
    backlog #9's "deflated-Sharpe / multiple-testing-corrected bar"
    means concretely — a strategy's raw in-sample Sharpe must clear
    this, not zero, to be worth a holdout pass.
    """
    benchmark = expected_max_sharpe(n_trials, variance_of_sr)
    return probabilistic_sharpe_ratio(sr_observed, benchmark, n_obs,
                                       skew=skew, kurtosis=kurtosis)


# ---------------------------------------------------------------------------
# Uncertainty, robustness, and study helpers (comprehensiveness pass 2,
# 2026-07-04): every function here answers a question a results doc keeps
# having to answer by hand.
# ---------------------------------------------------------------------------

def sharpe_ci(curve: list[dict], *, n_boot: int = 1000, block: int = 21,
               seed: int = 7, ci: float = 0.95) -> dict:
    """Circular block-bootstrap confidence interval on annualized Sharpe.

    A 12-year Sharpe carries ~±0.3 of sampling noise; a results doc
    quoting the point estimate without an interval invites over-
    reading. Blocks (default 21 trading days) preserve short-range
    autocorrelation the iid bootstrap would destroy. Deterministic for
    a given seed — cite the seed in the results doc.
    """
    import random as _random
    equities = [c["equity"] for c in curve]
    rets = [equities[i] / equities[i - 1] - 1.0
            for i in range(1, len(equities)) if equities[i - 1] > 0]
    n = len(rets)
    if n < 2 * block:
        return {"n_obs": n, "sharpe": summarize(curve)["sharpe"],
                "lo": None, "hi": None,
                "note": f"need >= {2 * block} daily returns for block={block}"}
    rng = _random.Random(seed)

    def _sharpe(xs: list[float]) -> float:
        m, s, _, _ = _moments(xs)
        return (m / s) * math.sqrt(252) if s > 0 else 0.0

    boots = []
    n_blocks = math.ceil(n / block)
    for _ in range(n_boot):
        sample: list[float] = []
        for _ in range(n_blocks):
            start_i = rng.randrange(n)
            for k in range(block):
                sample.append(rets[(start_i + k) % n])   # circular
        boots.append(_sharpe(sample[:n]))
    boots.sort()
    alpha = (1 - ci) / 2
    lo_i = max(0, int(alpha * n_boot) - 1)
    hi_i = min(n_boot - 1, int((1 - alpha) * n_boot))
    return {"n_obs": n, "sharpe": _sharpe(rets),
            "lo": boots[lo_i], "hi": boots[hi_i],
            "n_boot": n_boot, "block": block, "seed": seed, "ci": ci}


def walk_forward_windows(days: list[str], *, train_days: int = 756,
                          test_days: int = 252,
                          step_days: Optional[int] = None) -> list[dict]:
    """Rolling train/test windows over a trading-day list.

    The holdout discipline generalized: instead of one in-sample/holdout
    split, K non-overlapping (by default) test windows each preceded by
    their own training window — the standard defense against 'the one
    split happened to flatter it'. Returns [{train: (d0, d1),
    test: (d2, d3)}, ...]; a window that doesn't fully fit is dropped,
    never truncated silently.
    """
    ds = sorted(str(d)[:10] for d in days)
    step = step_days if step_days is not None else test_days
    if train_days < 1 or test_days < 1 or step < 1:
        raise ValueError("train_days, test_days, and step_days must be >= 1")
    out = []
    i = 0
    while i + train_days + test_days <= len(ds):
        out.append({
            "train": (ds[i], ds[i + train_days - 1]),
            "test": (ds[i + train_days], ds[i + train_days + test_days - 1]),
        })
        i += step
    return out


def parameter_cliff_report(cells: list[dict]) -> list[dict]:
    """Overfit smell-test: is each cell's metric an isolated peak?

    `cells` = [{"params": {...}, "metric": float, ...}]. For every
    cell, finds its one-step neighbors (cells differing in exactly one
    param — adjacent value for numeric params, any other value for
    categorical ones) and reports the gap between the cell and its
    neighborhood. A real effect is a plateau: 65-day momentum working
    while 55 and 75 both fail is noise wearing a crown. Sorted by
    isolation (metric minus neighbor mean), worst offender first.
    """
    def _neighbors(a: dict, b: dict, numeric_steps: dict) -> bool:
        pa, pb = a["params"], b["params"]
        if set(pa) != set(pb):
            return False
        diff = [k for k in pa if pa[k] != pb[k]]
        if len(diff) != 1:
            return False
        k = diff[0]
        va, vb = pa[k], pb[k]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            vals = numeric_steps[k]
            ia, ib = vals.index(va), vals.index(vb)
            return abs(ia - ib) == 1
        return True   # categorical: every other value is a neighbor

    numeric_steps: dict = {}
    for c in cells:
        for k, v in c["params"].items():
            if isinstance(v, (int, float)):
                numeric_steps.setdefault(k, set()).add(v)
    numeric_steps = {k: sorted(v) for k, v in numeric_steps.items()}

    out = []
    for c in cells:
        neigh = [o["metric"] for o in cells
                 if o is not c and _neighbors(c, o, numeric_steps)]
        if not neigh:
            out.append({**c, "n_neighbors": 0, "neighbor_mean": None,
                        "isolation": None})
            continue
        nm = sum(neigh) / len(neigh)
        out.append({**c, "n_neighbors": len(neigh), "neighbor_mean": nm,
                    "neighbor_min": min(neigh), "isolation": c["metric"] - nm})
    return sorted(out, key=lambda r: (r["isolation"] is None,
                                       -(r["isolation"] or 0.0)))


def event_car(events: list[dict], bars_by_symbol: dict[str, list[dict]],
               benchmark_bars: list[dict], *, max_offset: int = 20,
               date_field: str = "public_date",
               symbol_field: str = "symbol",
               carry_last: bool = False) -> dict:
    """Cumulative abnormal return curves for an event population.

    The event-study engine for PITEventFeed populations (insider
    clusters, PEAD, lockups, tenders): entry at the close of the FIRST
    trading day strictly AFTER the event's public date (no same-day
    fill — the filing might post after hours), then per-offset
    CAR_k = (P_{t0+k}/P_{t0} - 1) - (B_{t0+k}/B_{t0} - 1) on total-
    return series where available. Events whose symbol has no bar in
    [public_date+1 ...] land in `unpriceable` — the mandatory
    survivorship disclosure, never silently dropped. Offsets with
    shrinking n (later offsets outrun the panel) report their own n.

    `carry_last=False` (default) drops an event from offsets beyond
    its final bar — correct when a series ending means missing data.
    `carry_last=True` freezes the stock leg at its final print while
    the benchmark keeps running — correct when the series ending IS
    the outcome (an acquired target cashing out at the deal price).
    For M&A-family populations the default silently drops exactly the
    successes; pick deliberately and say which in the results doc.
    """
    field = _price_field_by_symbol(bars_by_symbol)
    bench_days = sorted(str(b["date"])[:10] for b in benchmark_bars)
    bench_px = {}
    b_field = "close_total_return" if all(
        b.get("close_total_return") is not None for b in benchmark_bars
    ) and benchmark_bars else "close"
    for b in benchmark_bars:
        bench_px[str(b["date"])[:10]] = b[b_field]

    sums = [0.0] * (max_offset + 1)
    cars_at: list[list[float]] = [[] for _ in range(max_offset + 1)]
    unpriceable: list[dict] = []
    n_events = 0
    for ev in events:
        sym = ev.get(symbol_field)
        pub = str(ev.get(date_field, ""))[:10]
        bars = bars_by_symbol.get(sym)
        if not bars or not pub:
            unpriceable.append({"symbol": sym, "date": pub,
                                "why": "no bars for symbol"})
            continue
        series = [(str(b["date"])[:10], b[field[sym]]) for b in bars]
        entry_i = next((i for i, (d, _) in enumerate(series) if d > pub), None)
        if entry_i is None:
            unpriceable.append({"symbol": sym, "date": pub,
                                "why": "no bar after public date"})
            continue
        d0, p0 = series[entry_i]
        if d0 not in bench_px:
            unpriceable.append({"symbol": sym, "date": pub,
                                "why": f"benchmark missing entry day {d0}"})
            continue
        b0 = bench_px[d0]
        b_days_from = [d for d in bench_days if d >= d0]
        n_events += 1
        last_px = None
        for k in range(max_offset + 1):
            if k >= len(b_days_from):
                break
            bk = bench_px.get(b_days_from[k])
            if bk is None or p0 <= 0 or b0 <= 0:
                break
            if entry_i + k < len(series):
                last_px = series[entry_i + k][1]
            elif not carry_last or last_px is None:
                break
            # carry_last: the stock leg freezes at its final print (the
            # cash-out — an acquired target's deal price) while the
            # benchmark keeps running. Default drops the event instead —
            # correct for missing data, WRONG for M&A populations where
            # the series ending IS the outcome (the 14D9 attrition
            # lesson: 255/384 successes silently vanished by +25).
            car = (last_px / p0 - 1.0) - (bk / b0 - 1.0)
            cars_at[k].append(car)

    def _median(xs: list[float]) -> Optional[float]:
        if not xs:
            return None
        ys = sorted(xs)
        return ys[len(ys) // 2]

    return {
        "offsets": list(range(max_offset + 1)),
        "n": [len(c) for c in cars_at],
        "mean_car": [sum(c) / len(c) if c else None for c in cars_at],
        "median_car": [_median(c) for c in cars_at],
        "n_events_priced": n_events,
        "unpriceable": unpriceable,
        "coverage_note": (
            f"{n_events} events priced, {len(unpriceable)} unpriceable "
            "(listed) — unpriceable events are disproportionately delisted/"
            "distressed names; any positive mean CAR must survive that "
            "disclosure."),
    }


# ---------------------------------------------------------------------------
# Comprehensiveness pass 3 (2026-07-04): benchmarks, capacity, portfolio
# combination, drawdown distributions, and the lab bridge.
# ---------------------------------------------------------------------------

def benchmark_curve(bars: list[dict], *, initial: float = 1000.0) -> dict:
    """One benchmark's daily equity curve from canonical bars.

    Feed it SPY (or any ETF/name) bars from `shared.sharadar.ingest_symbols`
    / `to_shared_bars` and pass the resulting `curve` straight to
    `excess_stats`. Uses the total-return series only when every bar
    carries it (same whole-series rule as simulate); `price_field` in
    the result says which one was used — a results doc comparing a
    total-return strategy to a price-return benchmark is comparing
    apples to half an orange, so the field is surfaced, not buried.
    """
    ordered = sorted(bars, key=lambda b: str(b["date"])[:10])
    if not ordered:
        raise ValueError("benchmark_curve: no bars")
    field_name = ("close_total_return"
                  if all(b.get("close_total_return") is not None for b in ordered)
                  else "close")
    p0 = ordered[0][field_name]
    if p0 is None or p0 <= 0:
        raise ValueError("benchmark_curve: first bar has no usable price")
    curve = [{"date": str(b["date"])[:10],
              "equity": initial * b[field_name] / p0} for b in ordered]
    return {"curve": curve, "price_field": field_name,
            "stats": summarize(curve)}


def capacity_stats(trades: list[dict], bars_by_symbol: dict[str, list[dict]],
                    *, adv_window: int = 21,
                    participation_cap: float = 0.01) -> dict:
    """Fill-size vs liquidity: at what sleeve size does this stop existing?

    For every fill, participation = fill notional / trailing
    `adv_window`-day average dollar volume (window ends the day BEFORE
    the fill — what was knowable when the order was sized; a fill with
    no prior volume history uses its own day and is flagged). Reports
    the participation distribution, the share of fills above 1%/5%/10%
    of ADV, the worst offenders, and `implied_max_equity_multiple`: how
    many times larger the book could run before the p90 fill hits
    `participation_cap` (linear scaling — optimistic, since real
    impact is super-linear; treat it as an upper bound). Run this
    BEFORE any capital-gate conversation.
    """
    date_index: dict[str, dict[str, int]] = {}
    dollar_vol: dict[str, list[Optional[float]]] = {}
    for s, bars in bars_by_symbol.items():
        date_index[s] = {str(b["date"])[:10]: i for i, b in enumerate(bars)}
        dollar_vol[s] = [
            (float(b["close"]) * float(b["volume"]))
            if b.get("volume") is not None and b.get("close") is not None
            else None
            for b in bars]

    parts: list[dict] = []
    no_volume: list[dict] = []
    for t in trades:
        s = t["symbol"]
        i = date_index.get(s, {}).get(str(t["date"])[:10])
        notional = t["shares"] * t["price"]
        if i is None:
            no_volume.append({"symbol": s, "date": t["date"],
                              "why": "no bar on fill date"})
            continue
        window = [v for v in dollar_vol[s][max(0, i - adv_window):i]
                  if v is not None and v > 0]
        own_day = i < 1 or not window
        if own_day:
            window = [v for v in dollar_vol[s][i:i + 1] if v and v > 0]
        if not window:
            no_volume.append({"symbol": s, "date": t["date"],
                              "why": "no volume data in window"})
            continue
        adv = sum(window) / len(window)
        parts.append({"symbol": s, "date": t["date"], "side": t["side"],
                      "notional": notional, "adv": adv,
                      "participation": notional / adv,
                      "adv_from_own_day": own_day})
    if not parts:
        return {"n_fills": 0, "no_volume_fills": no_volume}
    ps = sorted(p["participation"] for p in parts)
    n = len(ps)

    def _pct(q: float) -> float:
        return ps[min(n - 1, int(q * n))]

    p90 = _pct(0.90)
    return {
        "n_fills": n,
        "participation_median": _pct(0.50),
        "participation_p90": p90,
        "participation_max": ps[-1],
        "share_above_1pct": sum(1 for p in ps if p > 0.01) / n,
        "share_above_5pct": sum(1 for p in ps if p > 0.05) / n,
        "share_above_10pct": sum(1 for p in ps if p > 0.10) / n,
        "worst_fills": sorted(parts, key=lambda p: -p["participation"])[:5],
        "implied_max_equity_multiple": (
            participation_cap / p90 if p90 > 0 else math.inf),
        "participation_cap": participation_cap,
        "no_volume_fills": no_volume,
    }


def combine_curves(curves: dict[str, list[dict]],
                    weights: Optional[dict[str, float]] = None) -> dict:
    """Combine N sleeve curves into one book, with the numbers that
    matter for a correlated-drawdown question.

    Aligns on common dates, rescales each sleeve to its weight of a
    $1,000 book at the first common date, sums. Reports the combined
    stats, the pairwise daily-return correlation matrix, and the
    diversification gap: combined max drawdown vs the weighted average
    of the sleeves' own max drawdowns (zero gap = the sleeves crash
    together and the 'diversification' is cosmetic — the July 3
    drawdown study's question, mechanized for simulated books).
    """
    names = sorted(curves)
    if len(names) < 2:
        raise ValueError("combine_curves needs >= 2 curves")
    if weights is None:
        weights = {s: 1.0 / len(names) for s in names}
    if abs(sum(weights.get(s, 0.0) for s in names) - 1.0) > 1e-6:
        raise ValueError("weights must sum to 1.0 across the given curves")
    eq = {s: {str(c["date"])[:10]: c["equity"] for c in curves[s]}
          for s in names}
    days = sorted(set.intersection(*(set(e) for e in eq.values())))
    if len(days) < 3:
        raise ValueError("fewer than 3 common dates across curves")
    scaled: dict[str, list[float]] = {}
    for s in names:
        base = eq[s][days[0]]
        if base <= 0:
            raise ValueError(f"curve {s} starts at non-positive equity")
        scaled[s] = [1000.0 * weights[s] * eq[s][d] / base for d in days]
    combined = [{"date": d, "equity": sum(scaled[s][i] for s in names)}
                for i, d in enumerate(days)]

    rets = {s: [scaled[s][i] / scaled[s][i - 1] - 1.0
                for i in range(1, len(days))] for s in names}
    corr: dict[str, dict[str, float]] = {a: {} for a in names}
    for a in names:
        for b in names:
            ma = sum(rets[a]) / len(rets[a])
            mb = sum(rets[b]) / len(rets[b])
            va = sum((x - ma) ** 2 for x in rets[a])
            vb = sum((x - mb) ** 2 for x in rets[b])
            cov = sum((rets[a][i] - ma) * (rets[b][i] - mb)
                      for i in range(len(rets[a])))
            corr[a][b] = cov / math.sqrt(va * vb) if va > 0 and vb > 0 else 0.0

    per_sleeve = {s: summarize([{"date": days[i], "equity": scaled[s][i]}
                                 for i in range(len(days))]) for s in names}
    combined_stats = summarize(combined)
    wavg_dd = sum(weights[s] * per_sleeve[s]["max_drawdown"] for s in names)
    return {
        "curve": combined,
        "stats": combined_stats,
        "per_sleeve_stats": per_sleeve,
        "correlations": corr,
        "weighted_avg_max_drawdown": wavg_dd,
        "diversification_gap": combined_stats["max_drawdown"] - wavg_dd,
    }


def _block_bootstrap(rets: list[float], length: int, block: int, rng) -> list[float]:
    out: list[float] = []
    n = len(rets)
    while len(out) < length:
        start = rng.randrange(n)
        for k in range(block):
            out.append(rets[(start + k) % n])
    return out[:length]


def drawdown_distribution(curve: list[dict], *, n_sims: int = 1000,
                           block: int = 21, seed: int = 7,
                           thresholds: tuple = (0.20, 0.30, 0.40)) -> dict:
    """Max-drawdown DISTRIBUTION via block-bootstrap resequencing.

    The realized curve shows one path's drawdown; circuit-breaker
    calibration needs the distribution — the same returns in unluckier
    order. Resamples daily returns in blocks (preserving short-range
    clustering), rebuilds n_sims equity paths of the same length, and
    reports drawdown percentiles plus P(maxDD worse than each
    threshold). Deterministic per seed. Caveat: bootstrap scrambles
    LONG-range regime structure, so treat tail probabilities as a
    floor, not gospel — crashes cluster harder than blocks remember.
    """
    import random as _random
    equities = [c["equity"] for c in curve]
    rets = [equities[i] / equities[i - 1] - 1.0
            for i in range(1, len(equities)) if equities[i - 1] > 0]
    n = len(rets)
    if n < 2 * block:
        return {"n_obs": n,
                "note": f"need >= {2 * block} daily returns for block={block}"}
    rng = _random.Random(seed)

    def _max_dd(path_rets: list[float]) -> float:
        eq, peak, dd = 1.0, 1.0, 0.0
        for r in path_rets:
            eq *= 1 + r
            peak = max(peak, eq)
            dd = min(dd, eq / peak - 1.0)
        return dd

    dds = sorted(_max_dd(_block_bootstrap(rets, n, block, rng))
                 for _ in range(n_sims))

    def _pct(q: float) -> float:
        return dds[min(n_sims - 1, int(q * n_sims))]

    return {
        "n_obs": n, "n_sims": n_sims, "block": block, "seed": seed,
        "realized_max_drawdown": summarize(curve)["max_drawdown"],
        "dd_p50": _pct(0.50), "dd_p10": _pct(0.10), "dd_p05": _pct(0.05),
        "dd_worst": dds[0],
        "prob_worse_than": {f"{int(t * 100)}pct":
                             sum(1 for d in dds if d < -t) / n_sims
                             for t in thresholds},
    }


def draft_bias_checklist(result: dict, *, n_trials: int,
                          cost: CostModel, panel_note: str,
                          split_note: str, hypotheses_ever: int,
                          regime_boundaries: Optional[list[str]] = None) -> dict:
    """Draft the lab's eight bias-checklist answers from a run's own
    artifacts — numbers generated, not remembered.

    Every draft embeds figures computed from `result` (a simulate()
    output): coverage disclosures, the deflated-Sharpe bar at
    `n_trials`, bootstrap CI, cost drag, per-regime splits, raw n.
    `panel_note` and `split_note` are the two facts the engine cannot
    know (where the data came from; what was frozen when). Drafts are
    STARTING POINTS for the record_backtest writing requirement — the
    session signing the record owns the final wording; the lab's >=60-
    char floor is met so a lazy session can't submit empty strings,
    but an unedited draft is only honest if every number in it is.
    Keys match shared.lab.BIAS_CHECKLIST exactly.
    """
    curve = result["curve"]
    stats = result["stats"]
    ci = sharpe_ci(curve)
    tno = turnover_stats(result["trades"], curve)
    pr_only = result.get("price_return_only_symbols", [])
    bar = expected_max_sharpe(n_trials)
    regime = (summarize_by_period(curve, regime_boundaries)
              if regime_boundaries else None)
    regime_txt = ("; ".join(f"{k}: sharpe {v['sharpe']:.2f}"
                             for k, v in regime.items())
                  if regime else "regime splits not computed — supply "
                  "regime_boundaries and report them")
    ci_txt = (f"bootstrap 95% CI [{ci['lo']:.2f}, {ci['hi']:.2f}]"
              if ci.get("lo") is not None else "CI unavailable (short series)")
    return {
        "survivorship": (
            f"Panel: {panel_note}. Delisted handling: bars run through each "
            f"name's final trading day; {len(pr_only)} symbol(s) marked "
            f"price-return-only (dividends missing): "
            f"{', '.join(pr_only[:10]) or 'none'}."),
        "look_ahead": (
            f"Structural: universe snapshots read only same-day rows; "
            f"select() sees bars trimmed to the signal date. {split_note}. "
            "Event feeds (if any) route through PITEventFeed keyed on "
            "public dates."),
        "selection": (
            f"{split_note}. The population/universe rule and every cell "
            "were enumerated in the prereg before any panel data was "
            "pulled; nothing was added after results were seen."),
        "multiple_testing": (
            f"n_trials={n_trials} enumerated this study; house counter "
            f"hypotheses_ever={hypotheses_ever}. Observed Sharpe "
            f"{stats['sharpe']:.2f} must clear expected max Sharpe "
            f"{bar:.2f} under {n_trials} null trials (deflated-Sharpe bar), "
            "not zero."),
        "overfitting": (
            f"Parameters per cell fixed by prereg; {split_note}. "
            f"Sharpe {stats['sharpe']:.2f} with {ci_txt}; "
            "parameter_cliff_report on the grid distinguishes plateaus "
            "from isolated peaks before any cell is believed."),
        "costs_liquidity": (
            f"CostModel commission {cost.commission_bps}bps + slippage "
            f"{cost.slippage_bps}bps per side, min ticket ${cost.min_ticket}; "
            f"realized annual turnover {tno.get('annual_turnover', 0):.2f}x, "
            f"cost drag {tno.get('cost_drag_bps_yr', 0):.0f}bps/yr. "
            "Survivor reruns at 2x slippage required before any verdict."),
        "regime": (
            f"Window covers {curve[0]['date']}..{curve[-1]['date']}; "
            f"per-regime: {regime_txt}. Any edge concentrated in one "
            "segment is regime beta until shown otherwise."),
        "small_n": (
            f"n_obs={stats['n_obs']} daily returns; Sharpe "
            f"{stats['sharpe']:.2f} ({ci_txt}); total return "
            f"{stats['total_return']:.1%}. Forward validation still "
            "requires >=20 graded paper trades on the shrunk mean "
            "regardless of in-sample n."),
    }
