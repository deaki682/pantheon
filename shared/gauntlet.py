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

    cash = initial_cash
    positions: dict[str, float] = {}
    last_price: dict[str, float] = {}
    curve: list[dict] = []
    trades: list[dict] = []

    for day in all_days:
        for s, bars in bars_by_symbol.items():
            for b in bars:
                if b["date"] == day:
                    last_price[s] = b[price_field[s]]

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
            trimmed = _trim(bars_by_symbol, signal_day)
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
                                "cost": cost_amt})
            # Then buys, bounded by cash actually on hand. When cash
            # (after costs) can't cover every buy, all buys scale
            # pro-rata — a sequential fill would silently short-change
            # whichever symbol sorts last.
            buy_deltas: dict[str, float] = {}
            for s in all_syms:
                tgt = target_value.get(s, 0.0)
                px = last_price.get(s)
                cur_shares = positions.get(s, 0.0)
                if px is None or px <= 0:
                    continue
                delta = tgt - cur_shares * px
                if delta < cost.min_ticket:
                    continue
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
                positions[s] = positions.get(s, 0.0) + shares_bought
                trades.append({"date": day, "symbol": s, "side": "buy",
                                "shares": shares_bought, "price": px,
                                "cost": cost_amt})

        equity = cash + sum(positions[s] * last_price.get(s, 0.0)
                             for s in positions)
        curve.append({"date": day, "equity": equity})

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
