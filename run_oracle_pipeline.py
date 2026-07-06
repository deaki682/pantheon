"""Unified Oracle sourcing pipeline (2026-07-06 integration rebuild).

Replaces the ad-hoc, partially-wired sourcing path the audit found broken
(docs/oracle_pipeline_audit_2026-07-06.md). ONE runner that:

  1. loads the Sharadar panel once (SF1 latest+prior, DAILY marketcap $M->$,
     TICKERS meta with the FX-ambiguity collapse);
  2. runs BOTH data-complete legs through the FIXED screens — neglect
     (net_cash/ncav/tangible_book) AND asset_revaluation (land/resource/suspect
     NAV). (The forced_seller / hard_catalyst EDGAR legs are network-sourced and
     run separately; the 13D channel is a known data desert here.);
  3. merges + dedupes across legs with a PRINCIPLED floor precedence (a genuine
     countable cash floor wins; a tangible-book name that is really a land
     developer defers to its land-NAV record) — fixing the "47 names disagree on
     floor_type" dedup instability;
  4. ranks the FULL merged set PER FAMILY via oracle.fundability
     (net_cash / tangible_book / land_nav / suspect_nav / resource_nav), so the
     net-cash pile can no longer monopolize the verification budget and the land
     family (FPH) gets its own slots;
  5. writes the merged candidates AND the per-family verification queue.

Freshness reconciliation is applied by the assistant to the emitted queue via
MCP get_equity_fundamentals + oracle.freshness.apply_full_reconciliation (the
live broker feed is not importable in a script) — the queue is the hand-off.
"""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import neglect_screen as ns
from oracle import asset_revaluation as ar
from oracle import fundability as fb

NEG = "data/oracle_neglect"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"

# ---- panel: latest + prior SF1 per ticker ----------------------------------
sf1_rows = json.load(gzip.open(f"{NEG}/sf1_bs_part0.json.gz", "rt"))
by_ticker_rows: dict[str, list] = {}
for r in sf1_rows:
    t = r.get("ticker")
    if t:
        by_ticker_rows.setdefault(t, []).append(r)
sf1_by_ticker, prior_sharesbas = {}, {}
for t, rows in by_ticker_rows.items():
    rows.sort(key=lambda r: (r.get("datekey") or ""))
    sf1_by_ticker[t] = rows[-1]
    if len(rows) >= 2 and rows[-2].get("sharesbas"):
        prior_sharesbas[t] = float(rows[-2]["sharesbas"])
print(f"panel: {len(sf1_by_ticker)} tickers ({len(prior_sharesbas)} with a prior quarter)", flush=True)

# ---- current marketcap ($M -> $) -------------------------------------------
daily = json.load(gzip.open(DAILY, "rt"))
mcap_by_ticker, mcap_date = {}, {}
for r in daily:
    t, d = r.get("ticker"), r.get("date", "")
    if not t or r.get("marketcap") is None:
        continue
    if d > mcap_date.get(t, ""):
        mcap_date[t] = d
        mcap_by_ticker[t] = float(r["marketcap"]) * 1e6
print(f"marketcap: {len(mcap_by_ticker)} tickers", flush=True)

# ---- TICKERS meta (FX-ambiguity collapse: any non-USD row -> non-USD) -------
_raw_meta = json.load(open(f"{NEG}/tickers_meta.json"))
meta_by_ticker: dict[str, dict] = {}
for m in _raw_meta:
    t = m.get("ticker")
    if not t:
        continue
    cur = m.get("currency") or "USD"
    prev = meta_by_ticker.get(t)
    if prev is None:
        meta_by_ticker[t] = dict(m)
    else:
        if (prev.get("currency") or "USD") == "USD" and m.get("isdelisted") == "N":
            meta_by_ticker[t] = dict(m)
        if cur != "USD":
            meta_by_ticker[t]["currency"] = cur

# ---- exclude names already dossiered (CORRECT nesting — the audit fix) ------
exclude: set[str] = set()
for path in ("cache/oracle_convex_dossiers.json", "cache/oracle_dossiers.json"):
    if not os.path.exists(path):
        continue
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f"  WARN: could not read {path}: {e}", flush=True)
        continue
    # dossiers live UNDER data["dossiers"] (a list or dict), NOT at data.values()
    dossiers = data.get("dossiers", data) if isinstance(data, dict) else data
    rows = dossiers.values() if isinstance(dossiers, dict) else dossiers
    for d in rows:
        if isinstance(d, dict) and d.get("symbol"):
            exclude.add(d["symbol"].upper())
print(f"excluding {len(exclude)} already-dossiered names", flush=True)

# ---- run BOTH legs through the fixed screens -------------------------------
neg = ns.screen_panel(sf1_by_ticker, mcap_by_ticker, meta_by_ticker,
                      exclude_tickers=exclude, prior_sharesbas_by_ticker=prior_sharesbas)
ass = ar.screen_panel(sf1_by_ticker, mcap_by_ticker, meta_by_ticker, exclude_tickers=exclude)
print(f"neglect leg: {len(neg)} candidates | asset-reval leg: {len(ass)} candidates", flush=True)

# ---- merge with principled floor precedence --------------------------------
# A genuine countable-cash floor (net_cash/ncav) is the hardest true statement
# about a name -> the neglect record wins. But a name whose ONLY neglect floor is
# tangible_book AND which also has a land/resource NAV record is really an asset
# name -> defer to the asset-reval record (its land-NAV is the meaningful floor).
CASH_FLOORS = {"net_cash", "ncav"}
merged: dict[str, dict] = {}
for c in neg:
    merged[c["ticker"]] = c
for c in ass:
    t = c["ticker"]
    inc = merged.get(t)
    if inc is None:
        merged[t] = c
    elif inc.get("floor_type") not in CASH_FLOORS:
        merged[t] = c            # tangible_book neglect record yields to the land-NAV record
    # else: keep the hard cash floor
cands = list(merged.values())
print(f"merged: {len(cands)} unique candidates "
      f"({sum(1 for c in cands if c.get('floor_type') in CASH_FLOORS)} cash-floor)", flush=True)

# ---- per-family fundability ranking + verification queue -------------------
PER_FAMILY = int(os.environ.get("ORACLE_PER_FAMILY", "12"))
fams = fb.rank_by_family(cands, per_family=PER_FAMILY)
queue = fb.verification_queue(cands, per_family=PER_FAMILY)

json.dump({"spec": "oracle_pipeline", "ran": "2026-07-06",
           "n_candidates": len(cands), "candidates": cands},
          open("cache/oracle_pipeline_candidates.json", "w"), indent=1)
json.dump({"spec": "oracle_verification_queue", "per_family": PER_FAMILY,
           "families": {f: [c["ticker"] for c in rows] for f, rows in fams.items()},
           "queue": queue},
          open("cache/oracle_verification_queue.json", "w"), indent=1)

print("\n=== per-family verification queue (top %d each) ===" % PER_FAMILY, flush=True)
for fam in ("net_cash", "tangible_book", "land_nav", "suspect_nav", "resource_nav"):
    rows = fams.get(fam, [])
    if not rows:
        continue
    print(f"--- {fam} ---", flush=True)
    for i, c in enumerate(rows, 1):
        d = c.get("rank_discount")
        print(f"  {i}. {c['ticker']:6} prior={c['fundability']:.3f} "
              f"disc={ (d*100 if d is not None else 0):4.0f}% cap=${(c.get('marketcap_usd') or 0)/1e6:6.0f}M "
              f"{c.get('industry','')}", flush=True)
print(f"\nwrote cache/oracle_pipeline_candidates.json ({len(cands)}) "
      f"+ cache/oracle_verification_queue.json ({len(queue)} queued)", flush=True)
