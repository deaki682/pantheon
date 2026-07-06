"""Catalyst-overlay intersection — floor + catalyst (2026-07-06).

The measured lesson from the full three-leg verification
(docs/oracle_event_legs_verification_2026-07-06.md): the hard_catalyst leg is
NOT a standalone net (0 fundable of 14) — a catalyst is a bonus on a floor, never
a substitute. So the correct use of activist-13D / strategic-review signal is by
INTERSECTION with the neglect leg's already-floored names.

This finds the convex combo the mandate actually wants: a name trading below a
countable balance-sheet floor (the neglect leg) that ALSO has an activist who has
filed a Schedule 13D to force value realization (the catalyst overlay) — a floor
that something is actively working to unlock, unlike a value trap (RVP's founder
poison-pill) or a floorless catalyst (the 14 hard_catalyst kills).

Mechanism: enumerate every SC 13D / 13D-A subject company over the window from
EDGAR daily indexes (100% recall), map the neglect candidates ticker->CIK, and
intersect. A hit is a below-floor name with a fresh activist filing on it.

CAVEAT (measured on GNK): an SC 13D/A can be an ACQUIRER's TO-T filing (a hostile
tender), not a friendly value-realization activist — the intersection SURFACES
the overlap; the precision read still has to confirm the 13D is a friendly
campaign (Item 4) and the floor is real. This is a lead generator, not a decision.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oracle import forced_seller_sourcing as fss
from shared import edgar

DATE_FROM = sys.argv[1] if len(sys.argv) > 1 else "2026-04-06"
DATE_TO = sys.argv[2] if len(sys.argv) > 2 else "2026-07-06"

# Curated LIVE catalysts surfaced by the 2026-07-06 verification pass — names with
# a live value-realization catalyst that the sparse daily-index SC 13D enumeration
# does not capture (a strategic-review engagement, a proxy fight). Intersected with
# the neglect floors below. Refresh as verifications find new live catalysts.
KNOWN_LIVE_CATALYSTS = {
    "FULC": {"catalyst": "LIVE Leerink strategic-alternatives review (engaged 2026-05-31 after "
                         "85% RIF); sub-net-cash cash shell. Verified WATCH — reverse-merge-away risk.",
             "kind": "strategic_review"},
    "NNDM": {"catalyst": "LIVE Murchinson activist proxy fight (DEFC14A; EGM 2026-07-31) opposing a "
                         "biotech-pivot M&A that would spend the cash pile. Verified WATCH — thin floor, "
                         "governance-only demand (no capital-return yet).",
             "kind": "activist_proxy"},
}

# ---- neglect below-floor candidates (the hardened screen output) ----
neg_path = "cache/oracle_neglect_candidates.json"
if not os.path.exists(neg_path):
    print(f"run run_oracle_neglect_screen.py first ({neg_path} missing)"); sys.exit(1)
neg = json.load(open(neg_path))["candidates"]
neg_by_ticker = {c["ticker"]: c for c in neg if c.get("ticker")}
print(f"neglect below-floor names: {len(neg_by_ticker)}", flush=True)

# ---- ticker -> CIK for the neglect names ----
print("building ticker->CIK map (SEC)...", flush=True)
t2c = edgar.fetch_company_tickers()                       # {TICKER: cik10}
neg_cik = {t2c[t]: t for t in neg_by_ticker if t in t2c}  # {cik10: ticker}
print(f"  {len(neg_cik)} of {len(neg_by_ticker)} neglect names mapped to a CIK", flush=True)

# ---- enumerate SC 13D / 13D-A subjects over the window ----
print(f"enumerating SC 13D / 13D-A subjects {DATE_FROM}..{DATE_TO}...", flush=True)
raw13d = fss.enumerate_by_form(DATE_FROM, DATE_TO, ["SC 13D", "SC 13D/A"],
                               http_get=edgar.http_get)
print(f"  {len(raw13d)} distinct SC 13D/13D-A subject filers in window", flush=True)

# ---- intersect ----
overlay = []
for cik, ticker in neg_cik.items():
    if cik in raw13d:
        c = neg_by_ticker[ticker]
        e = raw13d[cik]
        overlay.append({
            "ticker": ticker, "cik": cik, "company": c.get("company"),
            "floor_type": c["floor_type"], "floor_basis": c["floor_basis"],
            "discount": c["discount"], "marketcap_usd": c["marketcap_usd"],
            "eroding_floor": c.get("eroding_floor"),
            "investments_heavy": c.get("investments_heavy"),
            "recent_dilution": c.get("recent_dilution"),
            "form_13d": sorted(e["forms"]), "filed_13d": e["last"],
            "note": "FLOOR + a fresh SC 13D — verify Item 4 is a FRIENDLY value-realization "
                    "campaign (not an acquirer TO-T) and the floor survives the four-trap gate.",
        })
# ---- curated live-catalyst intersection (from the verification pass) ----
curated = []
for tk, cat in KNOWN_LIVE_CATALYSTS.items():
    c = neg_by_ticker.get(tk)
    if not c:
        continue   # not currently below a floor -> not an intersection
    curated.append({
        "ticker": tk, "cik": t2c.get(tk), "company": c.get("company"),
        "floor_type": c["floor_type"], "floor_basis": c["floor_basis"],
        "discount": c["discount"], "marketcap_usd": c["marketcap_usd"],
        "eroding_floor": c.get("eroding_floor"), "investments_heavy": c.get("investments_heavy"),
        "catalyst_kind": cat["kind"], "catalyst": cat["catalyst"], "source": "curated_verification",
        "note": "FLOOR + a verified LIVE catalyst — the convex combo; drive through the four-trap gate.",
    })
curated.sort(key=lambda o: -o["discount"])

overlay.sort(key=lambda o: (-o["discount"]))

print(f"\n=== {len(curated)} FLOOR + VERIFIED-LIVE-CATALYST leads (curated) ===", flush=True)
for o in curated:
    print(f"  {o['ticker']:7s} {(o['company'] or '')[:30]:30s} {o['floor_type']:11s} "
          f"disc={o['discount']:+.0%} [{o['catalyst_kind']}] {o['catalyst'][:70]}...", flush=True)

print(f"\n=== {len(overlay)} FLOOR + FORM-ENUMERATED SC 13D overlay hits ===", flush=True)
for o in overlay:
    flags = "".join(f for f, on in (("E", o["eroding_floor"]), ("I", o["investments_heavy"]),
                                     ("D", o["recent_dilution"])) if on)
    print(f"  {o['ticker']:7s} {(o['company'] or '')[:34]:34s} {o['floor_type']:13s} "
          f"disc={o['discount']:+.0%} mcap=${o['marketcap_usd']/1e6:.0f}M "
          f"{o['form_13d']} filed {o['filed_13d']} [{flags}]", flush=True)
if not overlay:
    print("  (none this window — the environment's EDGAR 13D index is sparse; the "
          "machine is the deliverable, re-run on a wider/live window)", flush=True)

out = {"window": f"{DATE_FROM}..{DATE_TO}", "n_neglect": len(neg_by_ticker),
       "n_neglect_mapped": len(neg_cik), "n_13d_subjects": len(raw13d),
       "n_form_overlay": len(overlay), "form_overlay": overlay,
       "n_curated": len(curated), "curated_overlay": curated}
json.dump(out, open("cache/oracle_catalyst_overlay.json", "w"), indent=2)
print(f"\nwrote cache/oracle_catalyst_overlay.json "
      f"({len(curated)} curated + {len(overlay)} form-enumerated floor+catalyst leads)", flush=True)
