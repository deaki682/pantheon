"""Freshness reconciliation — pure-logic tests (2026-07-06, no network)."""
from oracle import freshness as fr


def _cand(ticker="TST", mcap=31e6, floor=202e6, disc=0.85):
    return {"ticker": ticker, "marketcap_usd": mcap, "floor_usd": floor,
            "discount": disc, "floor_type": "net_cash"}


def test_stale_marketcap_flips_fth_above_floor():
    # FTH: Sharadar $31M (stale 1.34M sh) -> Robinhood $590M (25.78M sh)
    out = fr.reconcile_marketcap(_cand("FTH", 31e6, 202e6, 0.85), 589.8e6)
    assert out["marketcap_source"] == "robinhood"
    assert out["stale_marketcap"] is True
    assert out["below_floor"] is False            # $590M > $202M floor
    assert out["marketcap_usd"] == round(589.8e6)
    assert out["discount"] < 0                     # a PREMIUM now, not a discount


def test_consistent_marketcap_not_flagged():
    # INVE: Sharadar $63M ~ Robinhood $62.8M -> consistent, kept
    out = fr.reconcile_marketcap(_cand("INVE", 63e6, 114e6, 0.45), 62.8e6)
    assert out["stale_marketcap"] is False
    assert out["below_floor"] is True
    assert out["marketcap_divergence"] < 0.20


def test_missing_broker_cap_keeps_sharadar():
    out = fr.reconcile_marketcap(_cand("XYZ"), None)
    assert out["marketcap_source"] == "sharadar"
    assert out["stale_marketcap"] is False
    assert out["below_floor"] is True


def test_apply_reconciliation_drops_stale():
    cands = [_cand("FTH", 31e6, 202e6, 0.85),
             _cand("INVE", 63e6, 114e6, 0.45),
             _cand("SEER", 89e6, 220e6, 0.60)]
    feed = {"FTH": 589.8e6, "INVE": 62.8e6, "SEER": 89e6}
    kept, dropped = fr.apply_reconciliation(cands, feed)
    assert {c["ticker"] for c in dropped} == {"FTH"}          # stale -> dropped
    assert {c["ticker"] for c in kept} == {"INVE", "SEER"}
    assert kept[0]["ticker"] == "SEER"                        # deepest reconciled discount first


def test_fundamentals_flags_negative_book_and_crypto():
    # FTH: negative book (pb -0.22) -> book_contradicts_floor
    fth = fr.reconcile_with_fundamentals(
        _cand("FTH", 31e6, 202e6, 0.85),
        {"market_cap": 589.8e6, "pb_ratio": "-0.2238", "description": "clinical-stage biopharma"})
    assert fth["book_contradicts_floor"] is True
    assert fth["crypto_treasury"] is False
    assert fr.is_clean(fth) is False              # dropped: above floor + neg book
    # AVX: name hides it, description reveals a crypto treasury
    avx = fr.reconcile_with_fundamentals(
        _cand("AVX", 42e6, 115e6, 0.63),
        {"market_cap": 41.9e6, "pb_ratio": "0.25",
         "description": "digital infrastructure ... mine Bitcoin ... Avalanche digital asset treasury"})
    assert avx["crypto_treasury"] is True
    assert fr.is_clean(avx) is False
    # LAWR: currency artifact -> pb 119 contradicts the "net cash" floor
    lawr = fr.reconcile_with_fundamentals(
        _cand("LAWR", 172e6, 606e6, 0.72),
        {"market_cap": 172e6, "pb_ratio": "119.05", "description": "AI and robotic tech, Tokyo"})
    assert lawr["book_contradicts_floor"] is True


def test_clean_candidate_passes_all_three():
    c = fr.reconcile_with_fundamentals(
        _cand("INVE", 63e6, 114e6, 0.45),
        {"market_cap": 62.8e6, "pb_ratio": "0.46", "description": "physical security / RFID"})
    assert fr.is_clean(c) is True


def test_asset_reval_uses_nav_floor():
    # asset-reval candidates key the floor as nav_at_cost_usd, not floor_usd
    c = {"ticker": "LAND", "marketcap_usd": 250e6, "nav_at_cost_usd": 400e6,
         "asset_coverage": 1.6}
    out = fr.reconcile_marketcap(c, 260e6)
    assert out["below_floor"] is True                          # $260M < $400M nav
    assert out["marketcap_source"] == "robinhood"


# --- 2026-07-06 audit fixes: is_clean fail-closed + full reconciliation ---
def test_is_clean_fails_closed_when_unreconciled():
    # a raw candidate that never went through reconciliation (no marketcap_source)
    # must NOT be reported clean
    assert fr.is_clean({"ticker": "RAW", "below_floor": True}) is False
    # once reconciled and still below floor, clean
    rec = fr.reconcile_marketcap(_cand("INVE", 63e6, 114e6, 0.45), 62.8e6)
    assert fr.is_clean(rec) is True


def test_apply_full_reconciliation_runs_all_three_checks():
    cands = [_cand("INVE", 63e6, 114e6, 0.45), _cand("AVX", 42e6, 115e6, 0.63)]
    feed = {"INVE": {"market_cap": 62.8e6, "pb_ratio": "0.46", "description": "RFID security"},
            "AVX": {"market_cap": 41.9e6, "pb_ratio": "0.25",
                    "description": "we mine Bitcoin, an Avalanche digital asset treasury"}}
    kept, dropped = fr.apply_full_reconciliation(cands, feed)
    assert "INVE" in [c["ticker"] for c in kept]
    assert "AVX" in [c["ticker"] for c in dropped]      # crypto caught by the full check
