"""Tests for proteus/dealflow.py — the odd-lot tender scanner.

Proteus v2 owns these (tests/test_proteus_*.py). Fixture clauses are
paraphrased from real SC TO-I boilerplate.
"""
import json

from proteus import dealflow


ODD_LOT_CLAUSE = (
    "Upon the terms and subject to the conditions of the Offer, if more "
    "than 4,000,000 Shares are properly tendered, we will purchase Shares "
    "in the following order of priority: first, all Shares properly "
    "tendered by any Odd Lot Holder (a holder of fewer than 100 shares) "
    "who tenders all of such holder's Shares; such Shares will not be "
    "subject to proration."
)

ODD_LOT_NO_PRIORITY = (
    "Brokerage commissions on transactions in odd lots may be somewhat "
    "higher than commissions charged on round lot transactions. "
    + "x" * 700 +
    " Proration, if required, will apply to all tendering shareholders."
)

FIXED_PRICE_TEXT = (
    "We are offering to purchase up to 2,500,000 shares of our common "
    "stock at a purchase price of $14.50 per share, net to the seller in "
    "cash. The Offer will expire at 5:00 p.m., New York City time, on "
    "Friday, August 14, 2026, unless extended."
)

DUTCH_TEXT = (
    "We invite shareholders to tender shares at prices not less than "
    "$21.00 nor more than $24.00 per share. The tender offer expires "
    "at 12:00 midnight on September 1, 2026."
)


class TestOddLotDetection:
    def test_priority_clause_detected(self):
        assert dealflow.has_odd_lot_priority(ODD_LOT_CLAUSE) is True

    def test_fewer_than_100_shares_alone_with_priority(self):
        txt = ("Holders of fewer than 100 shares who tender all their "
               "shares will be accepted for payment first.")
        assert dealflow.has_odd_lot_priority(txt) is True

    def test_odd_lot_mention_without_priority_rejected(self):
        assert dealflow.has_odd_lot_priority(ODD_LOT_NO_PRIORITY) is False

    def test_no_mention(self):
        assert dealflow.has_odd_lot_priority(
            "We will purchase all shares validly tendered.") is False

    def test_priority_language_far_away_not_matched(self):
        # priority context outside the +/-600 char window must not count
        txt = "odd lot holders exist." + " y" * 800 + " without proration."
        assert dealflow.has_odd_lot_priority(txt) is False


class TestOfferPrice:
    def test_fixed(self):
        p = dealflow.extract_offer_price(FIXED_PRICE_TEXT)
        assert p == {"kind": "fixed", "low": 14.50, "high": 14.50}

    def test_dutch(self):
        p = dealflow.extract_offer_price(DUTCH_TEXT)
        assert p == {"kind": "dutch", "low": 21.00, "high": 24.00}

    def test_dutch_with_commas(self):
        txt = "at prices not less than $1,050.00 nor more than $1,100.00"
        p = dealflow.extract_offer_price(txt)
        assert p["kind"] == "dutch" and p["low"] == 1050.0 and p["high"] == 1100.0

    def test_unknown(self):
        p = dealflow.extract_offer_price("no numbers here")
        assert p["kind"] == "unknown" and p["low"] is None

    def test_inverted_dutch_range_rejected(self):
        txt = "at prices not less than $24.00 nor more than $21.00"
        assert dealflow.extract_offer_price(txt)["kind"] == "unknown"


class TestExpiration:
    def test_fixed_text(self):
        assert dealflow.extract_expiration(FIXED_PRICE_TEXT) == "2026-08-14"

    def test_dutch_text(self):
        assert dealflow.extract_expiration(DUTCH_TEXT) == "2026-09-01"

    def test_none(self):
        assert dealflow.extract_expiration("nothing expires") is None

    def test_invalid_date_returns_none(self):
        assert dealflow.extract_expiration(
            "will expire on February 30, 2026") is None


class TestConditionFlags:
    def test_flags(self):
        txt = ("The Offer is not subject to any financing condition. "
               "This is a going-private transaction under Rule 13e-3.")
        f = dealflow.condition_flags(txt)
        assert f["financing_condition"] is True
        assert f["going_private_13e3"] is True
        assert f["minimum_tender_condition"] is False


class TestFtsParsing:
    PAYLOAD = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_id": "0001193125-26-000001:doc1.htm",
                 "_source": {"ciks": ["0001327978"],
                             "display_names": ["Example Fund Inc."],
                             "root_forms": ["SC TO-I"],
                             "file_date": "2026-07-01"}},
                {"_id": "0001193125-26-000002:doc2.htm",
                 "_source": {"ciks": ["0000320193"],
                             "display_names": ["Example Corp."],
                             "file_type": "SC 14D9",
                             "file_date": "2026-07-02"}},
            ],
        }
    }

    def test_parse_hits(self):
        rows = dealflow.parse_hits(self.PAYLOAD)
        assert len(rows) == 2
        assert rows[0] == {
            "accession": "0001193125-26-000001", "doc": "doc1.htm",
            "cik": "1327978", "name": "Example Fund Inc.",
            "form": "SC TO-I", "filed": "2026-07-01"}
        assert rows[1]["form"] == "SC 14D9"

    def test_doc_url(self):
        rows = dealflow.parse_hits(self.PAYLOAD)
        url = dealflow.doc_url(rows[0])
        assert url == ("https://www.sec.gov/Archives/edgar/data/1327978/"
                       "000119312526000001/doc1.htm")

    def test_doc_url_missing_fields(self):
        assert dealflow.doc_url({"cik": "", "accession": "", "doc": ""}) == ""

    def test_dedupe(self):
        rows = dealflow.parse_hits(self.PAYLOAD)
        assert len(dealflow.dedupe(rows + rows)) == 2

    def test_empty_payload(self):
        assert dealflow.parse_hits({}) == []


class TestEnrich:
    def test_enrich_attaches_terms(self):
        rec = {"accession": "a", "doc": "d", "cik": "1", "name": "X",
               "form": "SC TO-I", "filed": "2026-07-01"}
        out = dealflow.enrich(rec, ODD_LOT_CLAUSE + " " + FIXED_PRICE_TEXT)
        assert out["odd_lot_priority"] is True
        assert out["offer"]["kind"] == "fixed"
        assert out["expiration"] == "2026-08-14"
        assert rec.get("offer") is None  # input not mutated


class TestBestDocument:
    def test_prefers_offer_named_exhibit(self):
        files = [
            {"name": "cover.htm", "size": 9000},
            {"name": "d12345dex99a1a.htm", "size": 400000},
            {"name": "big-financials.htm", "size": 900000},
        ]
        assert dealflow.best_document(files) == "d12345dex99a1a.htm"

    def test_falls_back_to_largest_html(self):
        files = [
            {"name": "one.htm", "size": 100},
            {"name": "two.htm", "size": 5000},
            {"name": "image.jpg", "size": 999999},
        ]
        assert dealflow.best_document(files) == "two.htm"

    def test_no_html(self):
        assert dealflow.best_document([{"name": "a.txt", "size": 5}]) == ""

    def test_missing_size_tolerated(self):
        files = [{"name": "offer.htm"}, {"name": "offer2.htm", "size": 10}]
        assert dealflow.best_document(files) == "offer2.htm"

    def test_index_url(self):
        rec = {"cik": "1327978", "accession": "0001193125-26-000001"}
        assert dealflow.index_url(rec) == (
            "https://www.sec.gov/Archives/edgar/data/1327978/"
            "000119312526000001/index.json")

    def test_index_url_missing(self):
        assert dealflow.index_url({"cik": "", "accession": ""}) == ""


class TestEconomics:
    def test_positive_spread(self):
        e = dealflow.economics(14.50, 14.00, "2026-08-14", as_of="2026-07-11")
        assert e["shares"] == 99
        assert e["cost_basis"] == round(14.00 * 99, 2)
        assert e["worst_case_loss"] == e["cost_basis"]  # bounded loss = cost
        assert e["gross_profit"] == round(0.50 * 99, 2)
        # 34 days to expiry + 7 payment lag
        assert e["days_to_payment"] == 41
        assert e["annualized"] > 0

    def test_negative_spread_reads_negative(self):
        e = dealflow.economics(14.50, 15.00, None)
        assert e["gross_profit"] < 0 and e["annualized"] is None

    def test_zero_price_no_div_by_zero(self):
        e = dealflow.economics(1.0, 0.0, None)
        assert e["spread_pct"] == 0.0

    def test_expired_deal_no_annualization(self):
        e = dealflow.economics(10.0, 9.5, "2026-01-01", as_of="2026-07-11")
        assert e["annualized"] is None


class TestPersistence:
    def test_roundtrip(self, tmp_path):
        p = str(tmp_path / "df.json")
        data = {"updated": "2026-07-11", "candidates": [{"accession": "a"}]}
        dealflow.save(data, path=p)
        assert dealflow.load(path=p) == data
        assert json.load(open(p))["updated"] == "2026-07-11"

    def test_load_missing(self, tmp_path):
        assert dealflow.load(path=str(tmp_path / "nope.json")) == {
            "updated": "", "candidates": []}
