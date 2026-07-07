"""Oracle unified sourcing pass — all THREE why_mispriced legs (2026-07-06).

The coverage half of the two-stage machine. Sources the WHOLE universe across
every why_mispriced type the precision gate can fund, so nothing structurally
convex is left behind for lack of a net:

  1. FORCED_SELLER — form-enumerate every price-insensitive SUPPLY event
     (issuer tenders, fund wind-downs, large-cap spinoffs) off EDGAR daily
     indexes (measured 100% recall vs 12% keyword), tradability-split.
     [oracle.forced_seller_sourcing]

  2. HARD_CATALYST — form-enumerate every activist SC 13D / 13D-amendment
     (value-realization campaigns) + a strategic-review 8-K keyword supplement.
     Each 13D carries requires_item4_read (the index can't see a campaign).
     [oracle.hard_catalyst_sourcing]

  3. NEGLECT — screen the whole Sharadar fundamentals panel for names quietly
     trading below a countable floor (net cash / net-net / tangible book), with
     no event to trip a form index. FX-clean (USD reporters only), financials
     and mortgage-REITs excluded, cash-runway flagged. [oracle.neglect_screen]

Every candidate from every leg still faces the SAME precision gate
(make_convex_dossier -> verify_dossier -> rank_fundable). Coverage widens here;
precision keeps it honest downstream. Writes each leg's detail file plus a
combined cache/oracle_sourced_candidates.json the dossier stage reads.
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import forced_seller_sourcing as fss
from oracle import hard_catalyst_sourcing as hcs
from oracle import neglect_screen as ns

DATE_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-04-06"
DATE_TO = sys.argv[2] if len(sys.argv) > 2 else "2026-07-06"
NEG = "data/oracle_neglect"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"

# names already tracked (dossier pool / legacy cohort / nemesis pipeline)
exclude_ciks: set[str] = set()
exclude_tickers: set[str] = set()
if os.path.exists("cache/nemesis_pipeline.json"):
    try:
        exclude_ciks |= set(json.load(open("cache/nemesis_pipeline.json")).keys())
    except Exception:
        pass
for path in ("cache/oracle_convex_dossiers.json", "cache/oracle_dossiers.json"):
    if os.path.exists(path):
        try:
            data = json.load(open(path))
            items = data.values() if isinstance(data, dict) else data
            for d in items:
                if isinstance(d, dict) and d.get("symbol"):
                    exclude_tickers.add(d["symbol"].upper())
        except Exception:
            pass

print("building the listed-universe ticker map (SEC)...", flush=True)
c2t = fss.cik_to_ticker_map()
print(f"  {len(c2t)} listed CIKs (the tradability filter)\n", flush=True)

# ---- LEG 1: forced-seller events ------------------------------------------
print(f"[1/3] FORCED_SELLER — form-enumerating {DATE_FROM}..{DATE_TO} "
      f"(forms {sorted(fss.FORM_TO_FAMILY)})...", flush=True)
fs_all = fss.sweep_by_form(DATE_FROM, DATE_TO, cik_to_ticker=c2t,
                           exclude_ciks=exclude_ciks, tradable_only=False)
fs_tradable = [c for c in fs_all if c["tradable"]]
fs_nontradable = [c for c in fs_all if not c["tradable"]]
for c in fs_tradable:
    print(f"    {c['ticker'] or '?':7s} {c['company'][:38]:38s} "
          f"[{'+'.join(c['families'])}] {c['forms']} filed {c['first_filed']}", flush=True)
print(f"  -> {len(fs_tradable)} tradable (+{len(fs_nontradable)} non-tradable flagged)\n", flush=True)

# ---- LEG 2: hard catalysts (activist 13D + strategic review) ---------------
print(f"[2/3] HARD_CATALYST — form-enumerating SC 13D {DATE_FROM}..{DATE_TO}...", flush=True)
hc_all = hcs.sweep_by_form(DATE_FROM, DATE_TO, cik_to_ticker=c2t,
                           exclude_ciks=exclude_ciks, tradable_only=False)
hc_tradable = [c for c in hc_all if c["tradable"]]
hc_nontradable = [c for c in hc_all if not c["tradable"]]
try:
    hc_review = hcs.sweep_strategic_review(DATE_FROM, DATE_TO, exclude_ciks=exclude_ciks)
except Exception as e:
    print(f"    (strategic-review supplement skipped: {type(e).__name__})", flush=True)
    hc_review = []
for c in hc_tradable:
    print(f"    {c['ticker'] or '?':7s} {c['company'][:38]:38s} {c['forms']} "
          f"filed {c['last_filed']}  [Item-4 read required]", flush=True)
for c in hc_review:
    print(f"    {c.get('ticker') or '?':7s} {c['company'][:38]:38s} [strategic_review 8-K]", flush=True)
print(f"  -> {len(hc_tradable)} tradable 13D (+{len(hc_nontradable)} non-tradable) "
      f"+ {len(hc_review)} strategic-review\n", flush=True)

# ---- LEG 3: neglect (below-floor fundamentals screen) ----------------------
print(f"[3/3] NEGLECT — screening the Sharadar fundamentals panel...", flush=True)
neg_cands = []
try:
    sf1_rows = json.load(gzip.open(f"{NEG}/sf1_bs_part0.json.gz", "rt"))
    _by_ticker_rows: dict[str, list] = {}
    for r in sf1_rows:
        t = r.get("ticker")
        if t:
            _by_ticker_rows.setdefault(t, []).append(r)
    sf1_by_ticker: dict[str, dict] = {}
    prior_sharesbas: dict[str, float] = {}
    for t, rows in _by_ticker_rows.items():
        rows.sort(key=lambda r: (r.get("datekey") or ""))
        sf1_by_ticker[t] = rows[-1]
        if len(rows) >= 2 and rows[-2].get("sharesbas"):
            prior_sharesbas[t] = float(rows[-2]["sharesbas"])
    daily = json.load(gzip.open(DAILY, "rt"))
    mcap_by_ticker: dict[str, float] = {}
    mcap_date: dict[str, str] = {}
    for r in daily:
        t, d = r.get("ticker"), r.get("date", "")
        if t and r.get("marketcap") is not None and d > mcap_date.get(t, ""):
            mcap_date[t] = d
            mcap_by_ticker[t] = float(r["marketcap"]) * 1e6
    raw_meta = json.load(open(f"{NEG}/tickers_meta.json"))
    meta_by_ticker: dict[str, dict] = {}
    for m in raw_meta:                       # collapse multi-row tickers; any non-USD forces non-USD
        t = m.get("ticker")
        if not t:
            continue
        cur = m.get("currency") or "USD"
        if meta_by_ticker.get(t) is None:
            meta_by_ticker[t] = dict(m)
        elif (meta_by_ticker[t].get("currency") or "USD") == "USD" and m.get("isdelisted") == "N":
            meta_by_ticker[t] = dict(m)
        if cur != "USD":
            meta_by_ticker[t]["currency"] = cur
    neg_cands = ns.screen_panel(sf1_by_ticker, mcap_by_ticker, meta_by_ticker,
                                exclude_tickers=exclude_tickers,
                                prior_sharesbas_by_ticker=prior_sharesbas)
    by_type: dict[str, int] = {}
    for c in neg_cands:
        by_type[c["floor_type"]] = by_type.get(c["floor_type"], 0) + 1
    for c in neg_cands[:30]:
        flag = " ERODING" if c["eroding_floor"] else ""
        print(f"    {c['ticker'] or '?':7s} {(c['company'] or '')[:34]:34s} "
              f"{c['floor_type']:13s} disc={c['discount']:+.0%}{flag}", flush=True)
    if len(neg_cands) > 30:
        print(f"    ... +{len(neg_cands)-30} more", flush=True)
    print(f"  -> {len(neg_cands)} below-floor names ({by_type})\n", flush=True)
except FileNotFoundError:
    print(f"  (neglect panel not found under {NEG}/ — run run_oracle_neglect_pull.py first)\n", flush=True)

# ---- combined output -------------------------------------------------------
out = {
    "swept": f"{DATE_FROM}..{DATE_TO}",
    "method": "three-leg unified: forced_seller(form) + hard_catalyst(form+kw) + neglect(fundamentals)",
    "counts": {
        "forced_seller_tradable": len(fs_tradable),
        "hard_catalyst_tradable": len(hc_tradable),
        "hard_catalyst_review": len(hc_review),
        "neglect": len(neg_cands),
    },
    "forced_seller": {"tradable": fs_tradable, "nontradable_flagged": fs_nontradable},
    "hard_catalyst": {"tradable": hc_tradable, "nontradable_flagged": hc_nontradable,
                      "strategic_review": hc_review},
    "neglect": neg_cands,
}
json.dump(out, open("cache/oracle_sourced_candidates.json", "w"), indent=2)
total = len(fs_tradable) + len(hc_tradable) + len(hc_review) + len(neg_cands)
print(f"wrote cache/oracle_sourced_candidates.json — {total} actionable candidates "
      f"across 3 legs -> dossier->verify->rank_fundable pipeline", flush=True)
