"""Lens fetcher unit tests with stubbed HTTP."""
import json
from typing import Any

import pytest

from oracle import lenses
from oracle.lenses import (
    combine_lenses,
    fetch_insider_txns_for_symbol,
    fetch_quality_snapshot_for_symbol,
    find_latest_13fhr_accession,
    make_form4_fetcher,
    scan_universe_quality,
    search_recent_13d,
)


# Common Form 4 XML body
_F4 = """<?xml version="1.0"?>
<ownershipDocument>
  <issuer><issuerTradingSymbol>ACME</issuerTradingSymbol></issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>John Doe</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><officerTitle>CEO</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2024-05-30</value></transactionDate>
      <transactionAmounts>
        <transactionShares><value>1500</value></transactionShares>
        <transactionPricePerShare><value>10.00</value></transactionPricePerShare>
      </transactionAmounts>
      <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""


def _stub_http(routes: dict[str, str]):
    """Build an http_get stub that returns canned responses by URL substring."""
    def get(url, params=None, *, timeout=20.0):
        for key, body in routes.items():
            if key in url:
                return body
        raise RuntimeError(f"no stub for {url} (params={params})")
    return get


def test_fetch_insider_txns_for_symbol_happy_path():
    submissions = json.dumps({
        "cik": "1",
        "filings": {"recent": {
            "accessionNumber": ["acc-1"],
            "form": ["4"],
            "filingDate": ["2024-05-30"],
            "primaryDocument": ["doc.xml"],
            "items": [""],
        }},
    })
    routes = {
        "/submissions/CIK": submissions,
        "/Archives/edgar/data": _F4,
    }
    txns = fetch_insider_txns_for_symbol("ACME", "0000000001", today="2024-06-30", http=_stub_http(routes))
    assert len(txns) == 1
    assert txns[0].symbol == "ACME"
    assert txns[0].transaction_code == "P"


def test_fetch_insider_strips_xsl_viewer_prefix():
    # Form 4 primaryDocument is often the XSL viewer path, which serves HTML.
    # We must fetch the raw XML at the de-prefixed path instead.
    submissions = json.dumps({
        "cik": "1",
        "filings": {"recent": {
            "accessionNumber": ["acc-1"], "form": ["4"], "filingDate": ["2024-05-30"],
            "primaryDocument": ["xslF345X06/wk-form4_1.xml"], "items": [""],
        }},
    })
    seen_urls = []
    def get(url, params=None, *, timeout=20.0):
        seen_urls.append(url)
        return submissions if "/submissions/CIK" in url else _F4
    txns = fetch_insider_txns_for_symbol("ACME", "0000000001", today="2024-06-30", http=get)
    assert len(txns) == 1
    archive = next(u for u in seen_urls if "/Archives/edgar/data" in u)
    assert "xslF345X06" not in archive
    assert archive.endswith("/wk-form4_1.xml")


def test_fetch_insider_txns_swallows_fetch_error():
    def bad(url, params=None, *, timeout=20.0):
        raise RuntimeError("network down")
    assert fetch_insider_txns_for_symbol("ACME", "0000000001", http=bad) == []


def test_fetch_insider_txns_skips_non_xml_body():
    submissions = json.dumps({
        "cik": "1",
        "filings": {"recent": {
            "accessionNumber": ["acc-1"], "form": ["4"], "filingDate": ["2024-05-30"],
            "primaryDocument": ["doc.htm"], "items": [""],
        }},
    })
    routes = {
        "/submissions/CIK": submissions,
        "/Archives/edgar/data": "<html>not Form 4</html>",
    }
    txns = fetch_insider_txns_for_symbol("ACME", "0000000001", http=_stub_http(routes))
    assert txns == []


def test_fetch_insider_filters_by_cutoff_days():
    submissions = json.dumps({
        "cik": "1",
        "filings": {"recent": {
            "accessionNumber": ["acc-old"], "form": ["4"], "filingDate": ["2020-01-01"],
            "primaryDocument": ["doc.xml"], "items": [""],
        }},
    })
    routes = {"/submissions/CIK": submissions, "/Archives/edgar/data": _F4}
    txns = fetch_insider_txns_for_symbol(
        "ACME", "0000000001", days_back=60, today="2024-05-30", http=_stub_http(routes),
    )
    assert txns == []


def test_make_form4_fetcher_uses_cik_map():
    submissions = json.dumps({"cik": "1", "filings": {"recent": {
        "accessionNumber": ["a"], "form": ["4"], "filingDate": ["2024-05-30"],
        "primaryDocument": ["d.xml"], "items": [""],
    }}})
    routes = {"/submissions/CIK": submissions, "/Archives/edgar/data": _F4}
    fetcher = make_form4_fetcher({"ACME": "0000000001"}, today="2024-06-30", http=_stub_http(routes))
    assert len(fetcher("ACME")) == 1
    # Unknown ticker returns empty
    assert fetcher("UNKNOWN") == []


def test_find_latest_13fhr_accession():
    submissions = json.dumps({"cik": "1", "filings": {"recent": {
        "accessionNumber": ["acc-13F-1", "acc-other", "acc-13F-2"],
        "form": ["13F-HR", "10-K", "13F-HR"],
        "filingDate": ["2024-08-15", "2024-03-01", "2024-05-15"],
        "primaryDocument": ["d1.xml", "d2.htm", "d3.xml"],
        "items": ["", "", ""],
    }}})
    # parse_submissions_recent returns in input order; we want the first match
    acc = find_latest_13fhr_accession("0000000001", http=_stub_http({"/submissions/CIK": submissions}))
    assert acc == "acc-13F-1"


def test_find_latest_13fhr_none_when_no_filings():
    submissions = json.dumps({"cik": "1", "filings": {"recent": {
        "accessionNumber": ["a"], "form": ["10-K"], "filingDate": ["2024-01-01"],
        "primaryDocument": ["d"], "items": [""],
    }}})
    assert find_latest_13fhr_accession("0000000001", http=_stub_http({"/submissions/CIK": submissions})) is None


def test_search_recent_13d_filters_amendments_and_parses_ticker():
    # Real EDGAR FTS shape: `form` (string), `display_names` carries the ticker,
    # no `tickers`/`forms` fields. a2 is an amendment; a3 has no ticker.
    page1 = json.dumps({"hits": {"hits": [
        {"_id": "a1", "_source": {"form": "SCHEDULE 13D", "adsh": "a1", "ciks": ["1"],
            "display_names": ["Acme Inc.  (ACME)  (CIK 0000000001)"], "file_date": "2024-05-20"}},
        {"_id": "a2", "_source": {"form": "SCHEDULE 13D/A", "adsh": "a2", "ciks": ["2"],
            "display_names": ["Wid Corp  (WID)  (CIK 0000000002)"], "file_date": "2024-05-21"}},
        {"_id": "a3", "_source": {"form": "SCHEDULE 13D", "adsh": "a3", "ciks": ["3"],
            "display_names": ["Private Holdco Ltd  (CIK 0000000003)"], "file_date": "2024-05-22"}},
    ]}})
    empty = json.dumps({"hits": {"hits": []}})
    calls = [page1, empty]
    def get(url, params=None, *, timeout=20.0):
        return calls.pop(0) if calls else empty
    out = search_recent_13d(date_from="2024-05-01", date_to="2024-05-31", http=get)
    assert {f.accession_no for f in out} == {"a1", "a3"}  # amendment a2 dropped
    assert {f.symbol for f in out} == {"ACME", ""}  # a3 has no ticker


def test_search_recent_13d_query_params_avoid_edgar_500s():
    seen = []
    def get(url, params=None, *, timeout=20.0):
        seen.append(params or {})
        return json.dumps({"hits": {"hits": []}})
    search_recent_13d(date_from="2026-01-01", date_to="2026-01-07", http=get)
    p = seen[0]
    assert p["forms"] == "SCHEDULE 13D"  # SC 13D matches nothing on FTS
    assert "q" not in p  # empty q 500s — must be omitted entirely, never ""
    assert "from" not in p  # from=0 500s — page 0 omits it


def test_search_recent_13d_handles_empty():
    def get(*a, **k):
        return json.dumps({"hits": {"hits": []}})
    assert search_recent_13d(date_from="2024-05-01", date_to="2024-05-31", http=get) == []


def test_search_recent_13d_swallows_error():
    def boom(*a, **k):
        raise RuntimeError("nope")
    assert search_recent_13d(date_from="2024-05-01", date_to="2024-05-31", http=boom) == []


def test_fetch_quality_snapshot_passes_minimal():
    facts = {
        "Revenues": {"units": {"USD": [
            {"start": "2022-10-01", "end": "2022-12-31", "val": 100, "filed": "2023-02-01"},
            {"start": "2023-01-01", "end": "2023-03-31", "val": 110, "filed": "2023-05-01"},
            {"start": "2023-04-01", "end": "2023-06-30", "val": 120, "filed": "2023-08-01"},
            {"start": "2023-07-01", "end": "2023-09-30", "val": 130, "filed": "2023-11-01"},
        ]}},
        "NetIncomeLoss": {"units": {"USD": [
            {"start": "2022-10-01", "end": "2022-12-31", "val": 10, "filed": "2023-02-01"},
            {"start": "2023-01-01", "end": "2023-03-31", "val": 11, "filed": "2023-05-01"},
            {"start": "2023-04-01", "end": "2023-06-30", "val": 12, "filed": "2023-08-01"},
            {"start": "2023-07-01", "end": "2023-09-30", "val": 13, "filed": "2023-11-01"},
        ]}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [
            {"start": "2022-10-01", "end": "2022-12-31", "val": 15, "filed": "2023-02-01"},
            {"start": "2023-01-01", "end": "2023-03-31", "val": 15, "filed": "2023-05-01"},
            {"start": "2023-04-01", "end": "2023-06-30", "val": 15, "filed": "2023-08-01"},
            {"start": "2023-07-01", "end": "2023-09-30", "val": 15, "filed": "2023-11-01"},
        ]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            {"end": "2023-09-30", "val": 50, "filed": "2023-11-01"},
        ]}},
        "StockholdersEquity": {"units": {"USD": [
            {"end": "2023-09-30", "val": 100, "filed": "2023-11-01"},
        ]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": [
            {"end": "2023-09-30", "val": 1000000, "filed": "2023-11-01"},
        ]}},
    }
    payload = json.dumps({"facts": {"us-gaap": facts}})
    routes = {"/companyfacts/CIK": payload}
    out = fetch_quality_snapshot_for_symbol("ACME", "0000000001", http=_stub_http(routes))
    assert out["symbol"] == "ACME"
    assert out["snapshot"]["revenue_ttm"] == 460
    # Whether pass = True depends on data_quality being adequate
    assert isinstance(out["pass"], bool)


def test_fetch_quality_snapshot_fetch_failure():
    def boom(*a, **k):
        raise RuntimeError("404")
    out = fetch_quality_snapshot_for_symbol("ACME", "0000000001", http=boom)
    assert out["pass"] is False
    assert "fetch_failed" in out["reasons"]
    assert out["snapshot"] is None


def test_scan_universe_quality_checkpoints():
    calls = []
    def http(url, **k):
        return json.dumps({"facts": {"us-gaap": {}}})
    checkpoints = []
    sym_to_cik = {f"S{i}": str(i).zfill(10) for i in range(5)}
    out = scan_universe_quality(
        sym_to_cik, checkpoint_every=2,
        on_checkpoint=lambda n, rows: checkpoints.append(n),
        http=http,
    )
    assert len(out) == 5
    assert 2 in checkpoints and 4 in checkpoints


def test_scan_universe_quality_progress():
    seen = []
    sym_to_cik = {f"S{i}": str(i).zfill(10) for i in range(3)}
    scan_universe_quality(
        sym_to_cik, on_progress=lambda d, t: seen.append((d, t)),
        http=lambda *a, **k: json.dumps({"facts": {"us-gaap": {}}}),
    )
    assert seen == [(1, 3), (2, 3), (3, 3)]


def test_combine_lenses_includes_only_hit_symbols():
    out = combine_lenses(
        universe=["A", "B", "C"],
        insider_clusters=[{"symbol": "A"}],
        smart_money={"B": ["Berkshire"]},
        activist_symbols=["C"],
        quality_rows=[],
    )
    assert {r["symbol"] for r in out} == {"A", "B", "C"}


def test_combine_lenses_drops_universe_misses():
    out = combine_lenses(
        universe=["A", "B"],
        insider_clusters=[{"symbol": "A"}],
        smart_money={},
        activist_symbols=[],
    )
    assert {r["symbol"] for r in out} == {"A"}


def test_combine_lenses_quality_only_pass_counts():
    out = combine_lenses(
        universe=["A"],
        quality_rows=[{"symbol": "A", "pass": True, "snapshot": {}}],
    )
    assert len(out) == 1


def test_combine_lenses_quality_fail_doesnt_count():
    out = combine_lenses(
        universe=["A"],
        quality_rows=[{"symbol": "A", "pass": False, "snapshot": {}}],
    )
    assert out == []


def test_combine_lenses_ignores_quality_when_prescreen_failed():
    # Name pulled in by an insider cluster but failed the prescreen — its (sparse,
    # high-clamping) snapshot must NOT bank quality points.
    out = combine_lenses(
        universe=["A"],
        insider_clusters=[{"symbol": "A"}],
        quality_rows=[{"symbol": "A", "pass": False, "snapshot": {"dilution_yoy": 0.0}}],
    )
    assert len(out) == 1
    assert out[0]["lenses"]["quality"] == 0.0
    # A passing name with real coverage still earns quality.
    out2 = combine_lenses(
        universe=["B"],
        insider_clusters=[{"symbol": "B"}],
        quality_rows=[{"symbol": "B", "pass": True, "snapshot": {
            "gross_margin_ttm": 0.5, "operating_margin_ttm": 0.2, "revenue_yoy": 0.1}}],
    )
    assert out2[0]["lenses"]["quality"] > 0
