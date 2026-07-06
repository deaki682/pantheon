"""Backtest the Oracle composite ranker — does rank predict forward return?
(2026-07-06, the validation the red-team flagged as missing.)

POINT-IN-TIME + SURVIVORSHIP-FREE, and it reuses the ACTUAL ranker code
(oracle.upside_ranker.net_scores + composite_score) so we validate the real thing.

Data (already on disk, from the achilles gauntlet):
  SF1 ARQ  1998-2026  (ticker, datekey, calendardate, eps, revenue, shareswa, gp, ...)
  SEP      2000-2025  survivorship-free daily bars (ticker, date, closeadj) incl. delisted

Method:
  - rebalance at each quarter-end 2016..2024 (forward 12m available to 2025)
  - at date T, for each name use ONLY SF1 rows with datekey <= T (no look-ahead) to
    build the fundamental nets; SEP closeadj for the price nets + forward returns
  - nets ACTIVE here: acceleration (revenue), margin (gp/rev), earnings (eps YoY),
    recent_strength (~35d), range_reversal (252d). INACTIVE: value_floor (this SF1
    subset lacks equity/debt), special_situation (no historical event feed), thematic
    (current-only industry — included at low weight, minor look-ahead on sector label).
  - forward return market-relative = fwd - cross-sectional median fwd (removes beta).
    Delisted-before-forward names keep their LAST realized closeadj (anti-survivorship).
  - metric: per-date Spearman rank IC (composite vs fwd), pooled decile spread, IC t-stat.
"""
import gzip, json, glob, bisect, sys, os, math
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import upside_ranker as ur
from oracle.themes import tag_theme, ACTIVE_THEMES

START = "2014-06-30"     # earliest data we load (lookback for 2016 rebalances)
EXCL_SEC = {"Financial Services", "Real Estate"}

# ---- universe meta (exclude financials even if delisted; keep unknowns) ------
meta = {}
for m in json.load(open("data/oracle_neglect/tickers_meta.json")):
    t = m.get("ticker")
    if t and (t not in meta or m.get("isdelisted") == "N"):
        meta[t] = m


def excluded(t):
    m = meta.get(t)
    if not m:
        return False                      # unknown -> keep (many delisted names)
    if (m.get("currency") or "USD") != "USD":
        return True
    if m.get("sector") in EXCL_SEC or m.get("industry") == "Shell Companies":
        return True
    if (m.get("location") or "") in {"China", "Hong Kong"}:
        return True
    return False


# ---- SF1: per-ticker quarterly rows (datekey-sorted), datekey>=START ---------
print("loading SF1...", flush=True)
sf1 = {}
for p in sorted(glob.glob("data/achilles_gauntlet/sf1_arq_part*.json.gz")):
    for r in json.load(gzip.open(p, "rt")):
        t = r.get("ticker")
        if not t or excluded(t):
            continue
        dk = r.get("datekey")
        if not dk or dk < START:
            continue
        sf1.setdefault(t, []).append(r)
for t in sf1:
    sf1[t].sort(key=lambda r: r["datekey"])
print(f"  SF1: {len(sf1)} tickers", flush=True)

# ---- SEP: per-ticker (dates, closeadj), date>=START, only SF1 tickers --------
print("loading SEP (survivorship-free)...", flush=True)
sep = {}
for i, p in enumerate(sorted(glob.glob("data/achilles_gauntlet/sep_part*.json.gz"))):
    for r in json.load(gzip.open(p, "rt")):
        t = r.get("ticker")
        if t not in sf1:
            continue
        d = r.get("date")
        ca = r.get("closeadj")
        if not d or d < START or ca is None:
            continue
        sep.setdefault(t, ([], []))[0].append((d, ca))
    print(f"  SEP part {i} loaded", flush=True)
for t in list(sep):
    rows = sorted(sep[t][0])
    sep[t] = ([d for d, _ in rows], [c for _, c in rows])
print(f"  SEP: {len(sep)} tickers", flush=True)


def px_asof(t, target, max_stale=10):
    """closeadj on the latest trading day <= target (None if >max_stale days old)."""
    ds, cs = sep.get(t, ([], []))
    i = bisect.bisect_right(ds, target) - 1
    if i < 0:
        return None
    if (date.fromisoformat(target) - date.fromisoformat(ds[i])).days > max_stale:
        return None
    return cs[i]


def px_forward(t, target, tol_after=45):
    """closeadj at the first trading day >= target (within tol); if the name
    delisted BEFORE target, use its LAST closeadj (realized delisting path)."""
    ds, cs = sep.get(t, ([], []))
    if not ds:
        return None
    i = bisect.bisect_left(ds, target)
    if i < len(ds) and (date.fromisoformat(ds[i]) - date.fromisoformat(target)).days <= tol_after:
        return cs[i]
    if ds[-1] < target:                    # delisted before the forward date -> realized last price
        return cs[-1]
    return None


def px_window_range(t, lo, hi):
    ds, cs = sep.get(t, ([], []))
    a = bisect.bisect_left(ds, lo); b = bisect.bisect_right(ds, hi)
    w = cs[a:b]
    return (min(w), max(w)) if w else (None, None)


def iso_add(d, days):
    return (date.fromisoformat(d) + timedelta(days=days)).isoformat()


# ---- rebalance dates: quarter-ends 2016..2024 -------------------------------
REBAL = [f"{y}-{mmdd}" for y in range(2016, 2025)
         for mmdd in ("03-31", "06-30", "09-30", "12-31")]


def spearman(xs, ys):
    n = len(xs)
    if n < 8:
        return None
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0]*n
        i = 0
        while i < n:
            j = i
            while j+1 < n and v[order[j+1]] == v[order[i]]:
                j += 1
            avg = (i+j)/2.0 + 1
            for k in range(i, j+1):
                r[order[k]] = avg
            i = j+1
        return r
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx)/n, sum(ry)/n
    cov = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a-mx)**2 for a in rx)); vy = math.sqrt(sum((b-my)**2 for b in ry))
    return cov/(vx*vy) if vx and vy else None


# ---- run the cross-sections -------------------------------------------------
ic6, ic12 = [], []
pooled = []      # (composite, fwd6_rel, fwd12_rel)
for T in REBAL:
    rows = []
    for t in sf1:
        recs = [r for r in sf1[t] if r["datekey"] <= T]
        if len(recs) < 5:
            continue
        recs = recs[-6:]
        rev = [r["revenue"] for r in recs if r.get("revenue") is not None]
        om = [r["gp"]/r["revenue"] for r in recs if r.get("revenue") and r.get("gp") is not None]
        eps = [r.get("eps") for r in recs if r.get("eps") is not None]
        pT = px_asof(t, T)
        if pT is None or pT <= 0:
            continue
        shares = recs[-1].get("shareswa")
        if not shares or shares <= 0:
            continue
        mcap = shares * pT
        if not (1e8 <= mcap <= 3e9):            # hunting ground
            continue
        pRec = px_asof(t, iso_add(T, -35), max_stale=12)
        lo, hi = px_window_range(t, iso_add(T, -365), T)
        row = {"symbol": t, "mcap": mcap, "coverage": None,
               "revenue": rev, "op_margin": om,
               "ret_recent": (pT/pRec - 1) if pRec else None}
        if len(eps) >= 5 and eps[-5] not in (None, 0):
            row["eps_yoy_improve"] = (eps[-1] - eps[-5]) / abs(eps[-5])
        if lo is not None and hi > lo:
            row["range_pos"] = max(0.0, min(1.0, (pT - lo)/(hi - lo)))
        th = tag_theme((meta.get(t) or {}).get("industry"), (meta.get(t) or {}).get("name") or "")
        if th:
            row["theme"] = th["theme"]; row["theme_strength"] = th["theme_strength"]
        f6 = px_forward(t, iso_add(T, 182)); f12 = px_forward(t, iso_add(T, 365))
        if f6 is None or f12 is None:
            continue
        rows.append((row, f6/pT - 1, f12/pT - 1))
    if len(rows) < 30:
        continue
    # cross-sectional median forward (beta removal)
    med6 = sorted(r[1] for r in rows)[len(rows)//2]
    med12 = sorted(r[2] for r in rows)[len(rows)//2]
    comps, r6, r12 = [], [], []
    for row, f6, f12 in rows:
        sc = ur.net_scores(row, ACTIVE_THEMES)
        c = ur.composite_score(sc)
        comps.append(c); r6.append(f6 - med6); r12.append(f12 - med12)
        pooled.append((c, f6 - med6, f12 - med12))
    s6, s12 = spearman(comps, r6), spearman(comps, r12)
    if s6 is not None:
        ic6.append(s6)
    if s12 is not None:
        ic12.append(s12); print(f"  {T}: n={len(rows):4d}  IC6={s6:+.3f}  IC12={s12:+.3f}", flush=True)

# ---- summary ----------------------------------------------------------------
def stats(ic):
    n = len(ic); m = sum(ic)/n
    sd = math.sqrt(sum((x-m)**2 for x in ic)/(n-1)) if n > 1 else 0
    t = m/(sd/math.sqrt(n)) if sd else 0
    return n, m, sd, t, sum(1 for x in ic if x > 0)/n


def deciles(pooled, idx):
    ps = sorted(pooled, key=lambda p: p[0])
    n = len(ps); out = []
    for d in range(10):
        chunk = ps[d*n//10:(d+1)*n//10]
        out.append(sum(p[idx] for p in chunk)/len(chunk))
    return out


print("\n==================== RANKER BACKTEST RESULT ====================", flush=True)
for label, ic in (("6-month", ic6), ("12-month", ic12)):
    n, m, sd, t, pos = stats(ic)
    print(f"{label} rank IC: mean {m:+.4f}  t={t:+.2f}  ({pos:.0%} of {n} dates positive)", flush=True)
d12 = deciles(pooled, 2)
print(f"\n12-mo market-relative return by composite DECILE (D1 worst rank .. D10 best):", flush=True)
for i, v in enumerate(d12, 1):
    print(f"  D{i:<2} {v:+.1%}", flush=True)
print(f"  TOP-minus-BOTTOM decile spread (12mo): {d12[-1]-d12[0]:+.1%}", flush=True)
print(f"\npooled name-observations: {len(pooled)}", flush=True)

json.dump({"spec": "oracle_ranker_backtest", "ran": "2026-07-06",
           "ic6": ic6, "ic12": ic12, "decile12_rel": d12,
           "n_obs": len(pooled), "rebal_dates": len(ic12),
           "note": "point-in-time, survivorship-free; nets active: acceleration/margin/"
                   "earnings-yoy/recent_strength/range_reversal/thematic; value_floor + "
                   "special_situation INACTIVE (data)."},
          open("cache/oracle_ranker_backtest.json", "w"), indent=1)
print("\nwrote cache/oracle_ranker_backtest.json", flush=True)
