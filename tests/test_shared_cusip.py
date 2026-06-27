"""CUSIP → ticker resolution tests (OpenFIGI + SEC name fallback), all offline."""
import json

from shared.cusip import (
    _pick_ticker,
    build_name_ticker_index,
    normalize_name,
    resolve_cusips_openfigi,
    resolve_ticker,
)
from oracle.smart_money import Holding, resolve_holdings, smart_money_holders


def test_pick_ticker_prefers_us_listing():
    data = [
        {"exchCode": "UA", "ticker": "AAPL"},
        {"exchCode": "US", "ticker": "AAPL"},
    ]
    assert _pick_ticker(data) == "AAPL"


def test_pick_ticker_falls_back_to_first():
    assert _pick_ticker([{"exchCode": "LN", "ticker": "VOD"}]) == "VOD"
    assert _pick_ticker([]) == ""


def test_pick_ticker_normalizes_share_class_slash_to_dash():
    # OpenFIGI returns BRK/B; SEC convention (and the screen universe) is BRK-B.
    assert _pick_ticker([{"exchCode": "US", "ticker": "BRK/B"}]) == "BRK-B"
    assert _pick_ticker([{"exchCode": "US", "ticker": "LEN/B"}]) == "LEN-B"


def test_resolve_cusips_openfigi_maps_and_batches():
    seen_batches = []

    def post(url, body, *, timeout=20.0):
        seen_batches.append([j["idValue"] for j in body])
        # Echo back a result aligned to the request order.
        out = []
        for j in body:
            tick = {"037833100": "AAPL", "594918104": "MSFT"}.get(j["idValue"])
            out.append({"data": [{"exchCode": "US", "ticker": tick}]} if tick else {"data": []})
        return json.dumps(out)

    m = resolve_cusips_openfigi(
        ["037833100", "594918104", "000000000"], post=post, batch_size=2,
    )
    assert m == {"037833100": "AAPL", "594918104": "MSFT"}  # unmappable omitted
    assert seen_batches == [["037833100", "594918104"], ["000000000"]]  # batched by 2


def test_resolve_cusips_openfigi_swallows_batch_error():
    def boom(url, body, *, timeout=20.0):
        raise RuntimeError("429 forever")
    assert resolve_cusips_openfigi(["037833100"], post=boom) == {}


def test_normalize_name_strips_suffixes_and_punctuation():
    assert normalize_name("AerCap Holdings N.V.") == normalize_name("AERCAP HOLDINGS NV")
    assert normalize_name("Apple Inc.") == "APPLE"
    assert normalize_name("Alphabet Inc. Class A") == "ALPHABET"


def test_build_name_ticker_index_from_raw_sec_rows():
    raw = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 1, "ticker": "AER", "title": "AerCap Holdings N.V."},
    }
    idx = build_name_ticker_index(raw)
    assert idx[normalize_name("AERCAP HOLDINGS NV")] == "AER"
    assert idx["APPLE"] == "AAPL"


def test_resolve_ticker_cusip_first_then_name():
    cusip_map = {"037833100": "AAPL"}
    name_index = {normalize_name("AerCap Holdings NV"): "AER"}
    # CUSIP wins
    assert resolve_ticker("037833100", "WHATEVER", cusip_map, name_index) == "AAPL"
    # Name fallback when CUSIP unknown
    assert resolve_ticker("999", "AERCAP HOLDINGS N.V.", cusip_map, name_index) == "AER"
    # Neither resolves
    assert resolve_ticker("999", "Mystery Co", cusip_map, name_index) == ""


def test_resolve_holdings_end_to_end_keys_by_ticker():
    # Two holdings under a smart-money manager, identified by CUSIP + name only.
    by_manager = {
        "BERKSHIRE HATHAWAY": [
            Holding(symbol="", cusip="037833100", shares=100, value=1, name="APPLE INC"),
            Holding(symbol="", cusip="UNKNOWN", shares=50, value=1, name="AERCAP HOLDINGS NV"),
        ],
    }
    cusip_map = {"037833100": "AAPL"}
    name_index = {normalize_name("AerCap Holdings NV"): "AER"}
    resolve_holdings(by_manager, cusip_map=cusip_map, name_index=name_index)

    holders = smart_money_holders(by_manager)
    # Previously both holdings keyed by issuer NAME and never joined. Now tickers:
    assert "AAPL" in holders  # resolved via CUSIP
    assert "AER" in holders   # resolved via name fallback
    assert "APPLE INC" not in holders
