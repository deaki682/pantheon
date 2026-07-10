"""shared/field_prep.py — turn the on-disk Sharadar panel into cascade packets.

The read-cascade needs one `build_packet` per name for the WHOLE hunting ground.
This module assembles those packets from the survivorship-free on-disk data — SF1
balance-sheet/income rows, the daily-marketcap series, and the ticker-meta table —
so `shared.read_cascade.run_cascade` has a real field to read, not a schema.

It is deliberately split from the runner (`run_field_prep.py`, which does the gz
I/O): every function here operates on already-loaded plain rows, so the whole
assembly is unit-testable with tiny fixtures and never touches the network or the
filesystem. Pure in, packets out.

The exclusions are a parameter, not a hardcode, because the two gods hunt
different grounds off the SAME data: Oracle wants the under-covered small/mid-cap
non-financial ground (`ORACLE_FIELD`); Proteus wants the whole market
(`WHOLE_MARKET`). Same panel, two lenses on it.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from shared.read_cascade import build_packet

# Sharadar SF1 fundamentals are in ACTUAL DOLLARS; the daily table's marketcap is
# in $MILLIONS. Every cross-source ratio has to reconcile that, in one place.
MCAP_DOLLARS_PER_MUSD = 1_000_000.0
DOLLARS_PER_MUSD = 1_000_000.0
TREND_ARTIFACT_PCT = 200.0   # |recent trend| above this = split/share-count artifact, flag + sort last


@dataclass
class FieldOptions:
    """What ground to carve out of the panel, and how much history to pack."""
    exclude_sectors: frozenset = frozenset()
    exclude_industries: frozenset = frozenset()
    exclude_locations: frozenset = frozenset()
    require_usd: bool = True                 # drop non-USD reporters (FX-dirty floors)
    drop_delisted: bool = True               # keep only live names (isdelisted != 'Y')
    skip_symbols: frozenset = frozenset()    # e.g. the frozen legacy cohort
    revenue_quarters: int = 6                # how many trailing rev/margin points to pack
    recent_window: int = 25                  # daily bars back for the ~5wk trend
    min_mcap_musd: Optional[float] = None    # floor the marketcap (None = no floor)
    max_mcap_musd: Optional[float] = None    # ceiling (Oracle cedes mega-caps to quants)


# Oracle's under-covered small/mid-cap non-financial hunting ground.
ORACLE_FIELD = FieldOptions(
    exclude_sectors=frozenset({"Financial Services", "Real Estate"}),
    exclude_industries=frozenset({"Shell Companies"}),
    exclude_locations=frozenset({"China", "Hong Kong"}),
    require_usd=True, drop_delisted=True,
    max_mcap_musd=20_000.0,                  # ~$20B: above this the quants own the momentum
)

# Proteus hunts everything the broker will let him hold long.
WHOLE_MARKET = FieldOptions(
    exclude_industries=frozenset({"Shell Companies"}),
    require_usd=True, drop_delisted=True,
)


# --- meta -------------------------------------------------------------------
def index_meta(meta_rows: list) -> dict:
    """Latest meta row per ticker, preferring the live (non-delisted) record."""
    out: dict = {}
    for m in meta_rows:
        t = m.get("ticker")
        if not t:
            continue
        cur = out.get(t)
        if cur is None or (m.get("isdelisted") == "N" and cur.get("isdelisted") != "N"):
            out[t] = m
    return out


def meta_ok(t: str, meta: dict, opt: FieldOptions) -> bool:
    """Is this ticker inside the requested ground? Unknown meta -> keep (a live
    verify catches it); a KNOWN disqualifier -> drop."""
    m = meta.get(t)
    if not m:
        return True
    if opt.require_usd and (m.get("currency") or "USD") != "USD":
        return False
    if opt.drop_delisted and m.get("isdelisted") == "Y":
        return False
    if m.get("sector") in opt.exclude_sectors:
        return False
    if m.get("industry") in opt.exclude_industries:
        return False
    if (m.get("location") or "") in opt.exclude_locations:
        return False
    return True


# --- marketcap + recent trend (daily series) --------------------------------
def marketcap_series(daily_rows: list, *, recent_window: int = 25) -> tuple:
    """From daily {ticker,date,marketcap} rows: current marketcap (in $mm, the
    unit Sharadar reports) and the recent ~N-bar trend. Also returns the SPY-proxy
    median trend so a lens can say 'moving vs the field'."""
    series: dict = defaultdict(dict)
    for r in daily_rows:
        if r.get("ticker") and r.get("marketcap") is not None:
            series[r["ticker"]][r.get("date", "")] = float(r["marketcap"])
    all_dates = sorted({d for v in series.values() for d in v})
    if not all_dates:
        return {}, {}, 0.0, None
    d1 = all_dates[-1]
    d_recent = all_dates[-recent_window] if len(all_dates) >= recent_window else all_dates[0]
    mcap_musd: dict = {}
    ret_recent: dict = {}
    for t, v in series.items():
        if d1 in v and v[d1] > 0:
            mcap_musd[t] = v[d1]                          # already $mm
            if d_recent in v and v[d_recent] > 0:
                ret_recent[t] = v[d1] / v[d_recent] - 1.0
    trends = sorted(ret_recent.values())
    median = trends[len(trends) // 2] if trends else 0.0
    return mcap_musd, ret_recent, median, d1


# --- SF1 trajectories + balance-sheet floor inputs --------------------------
def _sf1_by_ticker(sf1_rows: list) -> dict:
    """Group SF1 rows by ticker, ONE row per calendardate (audit 2026-07-10):
    the ARQ pull carries restatement/amendment copies of the same quarter under
    distinct datekeys — 575/5593 tickers — which padded trajectories with
    duplicate quarters (a real acceleration read as a plateau) and let
    `rows[-1]` resolve to a superseded restatement. Keep the max-datekey copy
    per calendardate (the latest filed view of that quarter)."""
    best: dict = defaultdict(dict)
    for r in sf1_rows:
        t = r.get("ticker")
        if not t:
            continue
        cd = r.get("calendardate") or ""
        prev = best[t].get(cd)
        if prev is None or (r.get("datekey") or "") > (prev.get("datekey") or ""):
            best[t][cd] = r
    byt: dict = {}
    for t, by_cd in best.items():
        byt[t] = [by_cd[cd] for cd in sorted(by_cd)]
    return byt


def trajectories(rows: list, *, quarters: int = 6) -> dict:
    """Trailing revenue and net-margin trajectories from a ticker's sorted SF1
    rows — the shape a triage read needs to see 'is anything bending?'."""
    rev = [r.get("revenue") for r in rows if r.get("revenue") is not None]
    margin = [r["netinc"] / r["revenue"] for r in rows
              if r.get("revenue") and r["revenue"] > 0 and r.get("netinc") is not None]
    # revenue normalized to $mm (SF1 is in dollars) so the packet is compact/readable
    return {"revenue_trajectory": [round(float(x) / DOLLARS_PER_MUSD, 1) for x in rev[-quarters:]],
            "margin_trajectory": [round(float(x), 4) for x in margin[-quarters:]]}


def net_cash_ratio_pct(latest: dict, mcap_musd: Optional[float]) -> Optional[float]:
    """(cash+short-term investments − debt) / marketcap, as a percent. The cheap
    countable floor input the triage read leans on. SF1 cash/debt are in dollars;
    `mcap_musd` is in $mm — reconciled here so the ratio is a real percentage."""
    if not mcap_musd or mcap_musd <= 0:
        return None
    cash = (latest.get("cashneq") or 0.0) + (latest.get("investmentsc") or 0.0)
    debt = latest.get("debt") or 0.0
    mcap_dollars = mcap_musd * MCAP_DOLLARS_PER_MUSD
    return round((float(cash) - float(debt)) / mcap_dollars * 100.0, 2)


def screen_score(p: dict) -> float:
    """Arm-B screen: a DETERMINISTIC, model-free trajectory composite computed
    from packet fields alone (2026-07-10, replaces the dead lens_score). This is
    'the aim without the reading' — revenue acceleration primary, then the
    margin turn, then relative strength — so the A/B isolates the filing-
    grounded reading (Opus + BEAR×3) as the only difference between arms. An
    LLM confidence must NEVER be used here: both arms LLM-driven measures
    nothing (audit 2026-07-10)."""
    rev = [x for x in (p.get("revenue_trajectory") or []) if isinstance(x, (int, float))]
    mgn = [x for x in (p.get("margin_trajectory") or []) if isinstance(x, (int, float))]
    score = 0.0
    if len(rev) >= 3 and rev[-2] > 0 and rev[-3] > 0:
        g1 = rev[-1] / rev[-2] - 1.0
        g0 = rev[-2] / rev[-3] - 1.0
        score += max(-1.0, min(1.0, g1))                    # growth
        score += 0.5 * max(-1.0, min(1.0, g1 - g0))         # acceleration
    if len(mgn) >= 2:
        score += max(-1.0, min(1.0, mgn[-1] - mgn[-2]))     # margin delta
        if mgn[-2] < 0.0 <= mgn[-1]:
            score += 0.5                                     # the sign flip itself
    rt = p.get("recent_trend_pct")
    spy = p.get("spy_recent_trend_pct") or 0.0
    if rt is not None and abs(rt) <= TREND_ARTIFACT_PCT:
        score += max(-0.5, min(0.5, (rt - spy) / 100.0))    # relative strength
    return round(score, 4)


# --- assembly ---------------------------------------------------------------
def assemble_field(sf1_rows: list, daily_rows: list, meta_rows: list, *,
                   opt: FieldOptions = ORACLE_FIELD,
                   theme_tagger=None, special_symbols: Optional[set] = None) -> dict:
    """Assemble the whole field into cascade packets + an honest coverage report.

    Every in-ground ticker with a live marketcap becomes a packet or is counted in
    the drop tally with its reason — nothing vanishes silently, so the field the
    cascade reads is auditable. `theme_tagger(industry, name) -> {theme,
    theme_strength}|None` and `special_symbols` are optional lens inputs attached
    as packet extras.
    """
    meta = index_meta(meta_rows)
    mcap_musd, ret_recent, median_recent, as_of = marketcap_series(
        daily_rows, recent_window=opt.recent_window)
    byt = _sf1_by_ticker(sf1_rows)
    special = {s.upper() for s in (special_symbols or set())}

    packets: list = []
    drops = {"skip_symbols": 0, "meta_excluded": 0, "no_marketcap": 0,
             "below_min_mcap": 0, "above_max_mcap": 0}
    for t, rows in byt.items():
        if t in opt.skip_symbols:
            drops["skip_symbols"] += 1
            continue
        if not meta_ok(t, meta, opt):
            drops["meta_excluded"] += 1
            continue
        mc = mcap_musd.get(t)
        if mc is None:
            drops["no_marketcap"] += 1
            continue
        if opt.min_mcap_musd is not None and mc < opt.min_mcap_musd:
            drops["below_min_mcap"] += 1
            continue
        if opt.max_mcap_musd is not None and mc > opt.max_mcap_musd:
            drops["above_max_mcap"] += 1
            continue

        m = meta.get(t) or {}
        latest = rows[-1]
        traj = trajectories(rows, quarters=opt.revenue_quarters)
        extra: dict = {}
        if theme_tagger is not None:
            th = theme_tagger(m.get("industry"), m.get("name") or "")
            if th:
                extra["theme"] = th.get("theme")
                extra["theme_strength"] = th.get("theme_strength")
        if t.upper() in special:
            extra["special_situation"] = "event"
        rr = ret_recent.get(t)
        packets.append(build_packet(
            symbol=t, name=m.get("name") or "", sector=m.get("sector") or "",
            industry=m.get("industry") or "", mcap_musd=mc,
            revenue_trajectory=traj["revenue_trajectory"],
            margin_trajectory=traj["margin_trajectory"],
            recent_trend_pct=round(rr * 100.0, 2) if rr is not None else None,
            net_cash_ratio_pct=net_cash_ratio_pct(latest, mc),
            description="", filing_snippet="",
            spy_recent_trend_pct=round(median_recent * 100.0, 2),
            as_of=as_of, location=m.get("location") or "", **extra))

    # names with a live marketcap but no SF1 fundamentals never become packets —
    # count them (audit 2026-07-10: 141 vanished silently vs the docstring's claim)
    drops["no_sf1"] = sum(1 for t in mcap_musd if t not in byt)
    coverage = {"as_of": as_of, "n_packets": len(packets),
                "n_sf1_tickers": len(byt), "drops": drops,
                "median_recent_trend_pct": round(median_recent * 100.0, 2),
                "options": {"exclude_sectors": sorted(opt.exclude_sectors),
                            "exclude_industries": sorted(opt.exclude_industries),
                            "exclude_locations": sorted(opt.exclude_locations),
                            "require_usd": opt.require_usd, "drop_delisted": opt.drop_delisted,
                            "min_mcap_musd": opt.min_mcap_musd, "max_mcap_musd": opt.max_mcap_musd,
                            "revenue_quarters": opt.revenue_quarters}}
    # order best-known-first so a budget-bound cascade reads the liveliest names
    # first; the ordering is a hint, never a filter (every packet is still present).
    # |trend| > TREND_ARTIFACT_PCT is a reverse-split / thin-float / share-count
    # artifact (SMX +3275%): flag it and sort it LAST, never first (audit
    # 2026-07-10 — garbage names were occupying the cheapest read slots).
    for p in packets:
        rt = p.get("recent_trend_pct")
        if rt is not None and abs(rt) > TREND_ARTIFACT_PCT:
            p["trend_artifact"] = True

    def _order(p):
        rt = p.get("recent_trend_pct")
        junk = rt is None or p.get("trend_artifact", False)
        return (junk, -(rt or 0.0) if not junk else 0.0)

    packets.sort(key=_order)
    return {"packets": packets, "coverage": coverage}
