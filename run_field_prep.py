"""Field-prep runner — the on-disk Sharadar panel -> cascade packets on disk.

Deterministic and FREE (no model, no network): loads the survivorship-free SF1
balance-sheet rows, the daily-marketcap series, and the ticker-meta table, then
calls `shared.field_prep.assemble_field` once per god's ground and writes the
packet files the read-cascade will read. Run it before a cascade so the field is
current; re-run it after a fresh Sharadar pull.

  python3 run_field_prep.py            # both grounds
  python3 run_field_prep.py oracle     # just Oracle's
  python3 run_field_prep.py proteus    # just the whole market

Writes cache/oracle_field_packets.json and/or cache/proteus_field_packets.json
(packets + coverage). Nothing here spends a credit — the reads come later.
"""
import gzip, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.field_prep import ORACLE_FIELD, WHOLE_MARKET, assemble_field
from oracle.themes import tag_theme

SF1 = "data/oracle_neglect/sf1_bs_part0.json.gz"
DAILY = "data/achilles_gauntlet/daily_mcap_2026.json.gz"
META = "data/oracle_neglect/tickers_meta.json"
EVENT_CAL = "cache/shared_event_calendar.json"
LEGACY = frozenset({"CXT", "HDSN", "J", "PSN", "VITL"})   # frozen legacy cohort — never the engine's
SPECIAL_TYPES = {"spinoff", "ipo", "reorg_emergence", "post_reorg"}


def _load_rows():
    sf1 = json.load(gzip.open(SF1, "rt"))
    daily = json.load(gzip.open(DAILY, "rt"))
    meta = json.load(open(META))
    special = set()
    if os.path.exists(EVENT_CAL):
        ecd = json.load(open(EVENT_CAL))
        events = ecd.get("events", ecd) if isinstance(ecd, dict) else ecd
        for e in events:
            if isinstance(e, dict) and e.get("type") in SPECIAL_TYPES and e.get("symbol"):
                special.add(e["symbol"].upper())
    return sf1, daily, meta, special


def _write(path: str, ground: str, out: dict):
    payload = {"spec": "field_prep_packets", "ground": ground,
               "coverage": out["coverage"], "packets": out["packets"]}
    json.dump(payload, open(path, "w"))
    cov = out["coverage"]
    print(f"\n[{ground}] wrote {path}", flush=True)
    print(f"  packets={cov['n_packets']}  as_of={cov['as_of']}  "
          f"sf1_tickers={cov['n_sf1_tickers']}", flush=True)
    print(f"  drops={cov['drops']}", flush=True)
    top = out["packets"][:12]
    print("  liveliest 12 (by recent trend):", flush=True)
    for p in top:
        print(f"    {p['symbol']:6} mcap=${p['mcap_musd'] or 0:,.0f}mm  "
              f"trend={p.get('recent_trend_pct')}%  netcash={p.get('net_cash_ratio_pct')}%  "
              f"{(p.get('name') or '')[:28]}", flush=True)


def main():
    which = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    print("loading on-disk Sharadar panel...", flush=True)
    sf1, daily, meta, special = _load_rows()
    print(f"  sf1 rows={len(sf1):,}  daily rows={len(daily):,}  meta rows={len(meta):,}  "
          f"special={len(special)}", flush=True)

    if which in ("both", "oracle"):
        opt = ORACLE_FIELD.__class__(**{**ORACLE_FIELD.__dict__, "skip_symbols": LEGACY})
        out = assemble_field(sf1, daily, meta, opt=opt,
                             theme_tagger=tag_theme, special_symbols=special)
        _write("cache/oracle_field_packets.json", "oracle", out)

    if which in ("both", "proteus"):
        out = assemble_field(sf1, daily, meta, opt=WHOLE_MARKET,
                             theme_tagger=tag_theme, special_symbols=special)
        _write("cache/proteus_field_packets.json", "proteus", out)


if __name__ == "__main__":
    main()
