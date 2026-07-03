"""Tests for nemesis.spinoffs — the EDGAR Form 10-12B discovery pipeline.

The parser is tested against a faked full-text-search payload (the network
function search_spinoff_registrations is deliberately untested — it is a
one-line pipe of edgar.search_filings into the parser). Pipeline tests
focus on the two-writer contract: the auto sweep must never clobber
runbook-owned status or fields.
"""
import json
import os

from nemesis.spinoffs import (
    SpinEvent,
    events_from_search_payload,
    extract_ticker,
    load_pipeline,
    save_pipeline,
    update_pipeline,
)


# ------- extract_ticker -------


class TestExtractTicker:
    def test_ticker_and_cik(self):
        assert (
            extract_ticker("Versant Media Group, Inc.  (VSNT)  (CIK 0002067876)")
            == "VSNT"
        )

    def test_cik_only(self):
        assert extract_ticker("Cyprium Holdings Ltd  (CIK 0002078008)") is None

    def test_no_parens_at_all(self):
        assert extract_ticker("Plain Company Name Inc") is None

    def test_empty_string(self):
        assert extract_ticker("") is None

    def test_dotted_class_ticker(self):
        assert (
            extract_ticker("Berkshire Spinco  (BRK.B)  (CIK 0001067983)") == "BRK.B"
        )

    def test_multi_class_paren_takes_first(self):
        assert (
            extract_ticker("Dual Class Co  (DUAL.A, DUAL.B)  (CIK 0001111111)")
            == "DUAL.A"
        )

    def test_too_long_token_is_not_a_ticker(self):
        # 7+ uppercase chars in parens is a word, not a ticker.
        assert extract_ticker("Acme Corp  (HOLDINGS)  (CIK 0001234567)") is None

    def test_lowercase_token_is_not_a_ticker(self):
        assert extract_ticker("Acme Corp  (formerly Beta)  (CIK 0001234567)") is None

    def test_cik_paren_never_mistaken_for_ticker(self):
        # Even with no other parens, the CIK group must not yield "CIK".
        assert extract_ticker("Solo Co (CIK 123)") is None


# ------- events_from_search_payload -------


def _hit(display_name, file_date, cik=None):
    source = {"display_names": [display_name], "file_date": file_date}
    if cik is not None:
        source["cik"] = cik
    return {"_source": source}


def _fake_payload():
    """Three companies: one with a ticker and multiple filings (amendment
    trail, ticker only on the later display name), one CIK-only, one whose
    _source lacks 'cik' so it must be parsed from the display name."""
    return {
        "hits": {
            "total": {"value": 4},
            "hits": [
                # Versant: initial 10-12B (no ticker yet) + amendment (ticker).
                _hit(
                    "Versant Media Group, Inc.  (CIK 0002067876)",
                    "2026-03-02",
                    cik="2067876",
                ),
                _hit(
                    "Versant Media Group, Inc.  (VSNT)  (CIK 0002067876)",
                    "2026-05-18",
                    cik="2067876",
                ),
                # Cyprium: single filing, no ticker assigned yet.
                _hit(
                    "Cyprium Holdings Ltd  (CIK 0002078008)",
                    "2026-04-10",
                    cik="2078008",
                ),
                # Solstice: _source has no 'cik' key — parse from name.
                _hit(
                    "Solstice Advanced Materials Inc.  (SOLS)  (CIK 0002034201)",
                    "2026-01-15",
                ),
            ],
        }
    }


class TestEventsFromSearchPayload:
    def test_one_event_per_cik(self):
        events = events_from_search_payload(_fake_payload())
        assert len(events) == 3
        assert all(isinstance(e, SpinEvent) for e in events)

    def test_sorted_by_first_filed(self):
        events = events_from_search_payload(_fake_payload())
        assert [e.first_filed for e in events] == [
            "2026-01-15",
            "2026-03-02",
            "2026-04-10",
        ]

    def test_multiple_filings_merge_dates_and_count(self):
        events = events_from_search_payload(_fake_payload())
        versant = next(e for e in events if e.cik == "0002067876")
        assert versant.first_filed == "2026-03-02"
        assert versant.last_filed == "2026-05-18"
        assert versant.n_filings == 2

    def test_prefers_ticker_bearing_display_name(self):
        # The first Versant hit has no ticker; the amendment does. The
        # merged event must carry the ticker regardless of hit order.
        events = events_from_search_payload(_fake_payload())
        versant = next(e for e in events if e.cik == "0002067876")
        assert versant.ticker == "VSNT"
        assert versant.company == "Versant Media Group, Inc."

    def test_no_ticker_company(self):
        events = events_from_search_payload(_fake_payload())
        cyprium = next(e for e in events if e.cik == "0002078008")
        assert cyprium.ticker is None
        assert cyprium.company == "Cyprium Holdings Ltd"
        assert cyprium.n_filings == 1
        assert cyprium.first_filed == cyprium.last_filed == "2026-04-10"

    def test_cik_parsed_from_display_name_when_absent(self):
        events = events_from_search_payload(_fake_payload())
        solstice = next(e for e in events if e.ticker == "SOLS")
        assert solstice.cik == "0002034201"

    def test_ciks_are_zero_padded_to_10(self):
        events = events_from_search_payload(_fake_payload())
        assert all(len(e.cik) == 10 for e in events)
        assert all(e.cik.isdigit() for e in events)

    def test_empty_payload(self):
        assert events_from_search_payload({}) == []
        assert events_from_search_payload({"hits": {"hits": []}}) == []

    def test_hit_without_any_cik_is_skipped(self):
        payload = {
            "hits": {
                "hits": [_hit("Mystery Co with no CIK paren", "2026-02-01")]
            }
        }
        assert events_from_search_payload(payload) == []


# ------- pipeline persistence -------


class TestPipelinePersistence:
    def test_roundtrip(self, tmp_path):
        path = str(tmp_path / "nemesis_pipeline.json")
        pipeline = {
            "0002067876": {
                "company": "Versant Media Group, Inc.",
                "ticker": "VSNT",
                "status": "ticker_assigned",
                "first_seen": "2026-07-02",
            }
        }
        save_pipeline(path, pipeline)
        assert load_pipeline(path) == pipeline

    def test_save_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "pipeline.json")
        save_pipeline(path, {"0000000001": {"company": "X"}})
        assert load_pipeline(path) == {"0000000001": {"company": "X"}}

    def test_save_is_atomic_no_tmp_left_behind(self, tmp_path):
        path = str(tmp_path / "pipeline.json")
        save_pipeline(path, {})
        assert not os.path.exists(path + ".tmp")

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert load_pipeline(str(tmp_path / "nope.json")) == {}

    def test_corrupt_file_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "pipeline.json")
        with open(path, "w") as f:
            f.write("{not json at all")
        assert load_pipeline(path) == {}

    def test_wrong_shape_returns_empty_dict(self, tmp_path):
        path = str(tmp_path / "pipeline.json")
        with open(path, "w") as f:
            json.dump(["a", "list", "not", "a", "dict"], f)
        assert load_pipeline(path) == {}


# ------- update_pipeline -------


def _event(**overrides):
    base = dict(
        company="Versant Media Group, Inc.",
        cik="0002067876",
        ticker="VSNT",
        first_filed="2026-03-02",
        last_filed="2026-05-18",
        n_filings=2,
    )
    base.update(overrides)
    return SpinEvent(**base)


class TestUpdatePipeline:
    def test_creation_sets_first_seen_and_auto_status(self):
        pipeline = update_pipeline({}, [_event()], today="2026-07-02")
        entry = pipeline["0002067876"]
        assert entry["first_seen"] == "2026-07-02"
        assert entry["last_updated"] == "2026-07-02"
        assert entry["company"] == "Versant Media Group, Inc."
        assert entry["ticker"] == "VSNT"
        assert entry["first_filed"] == "2026-03-02"
        assert entry["last_filed"] == "2026-05-18"
        assert entry["n_filings"] == 2
        assert entry["status"] == "ticker_assigned"

    def test_no_ticker_means_registered(self):
        ev = _event(cik="0002078008", company="Cyprium Holdings Ltd", ticker=None)
        pipeline = update_pipeline({}, [ev], today="2026-07-02")
        entry = pipeline["0002078008"]
        assert entry["ticker"] is None
        assert entry["status"] == "registered"

    def test_update_keeps_first_seen_bumps_last_updated(self):
        pipeline = update_pipeline({}, [_event()], today="2026-07-02")
        update_pipeline(
            pipeline, [_event(last_filed="2026-06-20", n_filings=3)],
            today="2026-07-09",
        )
        entry = pipeline["0002067876"]
        assert entry["first_seen"] == "2026-07-02"
        assert entry["last_updated"] == "2026-07-09"
        assert entry["last_filed"] == "2026-06-20"
        assert entry["n_filings"] == 3

    def test_status_upgrades_registered_to_ticker_assigned(self):
        first = _event(ticker=None)
        pipeline = update_pipeline({}, [first], today="2026-07-02")
        assert pipeline["0002067876"]["status"] == "registered"
        update_pipeline(pipeline, [_event()], today="2026-07-09")
        assert pipeline["0002067876"]["status"] == "ticker_assigned"

    def test_ticker_never_erased_by_tickerless_event(self):
        # A narrow re-scan can hit only old display names without the
        # ticker; that must not forget the listing we already learned.
        pipeline = update_pipeline({}, [_event()], today="2026-07-02")
        update_pipeline(pipeline, [_event(ticker=None)], today="2026-07-09")
        entry = pipeline["0002067876"]
        assert entry["ticker"] == "VSNT"
        assert entry["status"] == "ticker_assigned"

    def test_runbook_status_never_downgraded(self):
        # The runbook marked the spinoff distributed; a later EDGAR sweep
        # (which knows nothing about distribution) must leave it alone.
        pipeline = update_pipeline({}, [_event()], today="2026-07-02")
        entry = pipeline["0002067876"]
        entry["status"] = "distributed"
        entry["distribution_date"] = "2026-06-30"
        entry["first_trade_date"] = "2026-07-01"
        entry["window_state"] = "waiting_for_dump"
        entry["dossier_verdict"] = "buy"

        update_pipeline(pipeline, [_event(n_filings=4)], today="2026-07-09")

        assert entry["status"] == "distributed"
        assert entry["distribution_date"] == "2026-06-30"
        assert entry["first_trade_date"] == "2026-07-01"
        assert entry["window_state"] == "waiting_for_dump"
        assert entry["dossier_verdict"] == "buy"
        # ...while the sweep-owned fields still refresh.
        assert entry["n_filings"] == 4
        assert entry["last_updated"] == "2026-07-09"

    def test_all_runbook_statuses_are_final(self):
        for status in ("distributed", "entered", "skipped", "expired"):
            pipeline = update_pipeline({}, [_event()], today="2026-07-02")
            pipeline["0002067876"]["status"] = status
            update_pipeline(pipeline, [_event()], today="2026-07-09")
            assert pipeline["0002067876"]["status"] == status

    def test_date_window_merge_never_shrinks_history(self):
        # First sweep covered Jan-Jun; a later narrow sweep only sees May.
        pipeline = update_pipeline({}, [_event()], today="2026-07-02")
        narrow = _event(
            first_filed="2026-05-18", last_filed="2026-05-18", n_filings=1
        )
        update_pipeline(pipeline, [narrow], today="2026-07-09")
        entry = pipeline["0002067876"]
        assert entry["first_filed"] == "2026-03-02"  # not shrunk forward
        assert entry["last_filed"] == "2026-05-18"
        assert entry["n_filings"] == 2  # max, not overwritten down

    def test_returns_the_mutated_pipeline(self):
        pipeline = {}
        out = update_pipeline(pipeline, [_event()], today="2026-07-02")
        assert out is pipeline

    def test_full_roundtrip_through_disk(self, tmp_path):
        path = str(tmp_path / "pipeline.json")
        events = events_from_search_payload(_fake_payload())
        pipeline = update_pipeline(load_pipeline(path), events, today="2026-07-02")
        save_pipeline(path, pipeline)
        reloaded = load_pipeline(path)
        assert set(reloaded) == {"0002067876", "0002078008", "0002034201"}
        assert reloaded["0002067876"]["status"] == "ticker_assigned"
        assert reloaded["0002078008"]["status"] == "registered"


# ------- extract_ticker: legal-name parens (2026-07-03 review fix) -------

class TestExtractTickerLegalNameParens:
    def test_jurisdiction_paren_is_not_a_ticker(self):
        # "(UK)" is part of the legal name — more name text follows it, so
        # it is not adjacent to the CIK group and must not read as a ticker.
        assert extract_ticker(
            "Global Industries (UK) Ltd  (CIK 0001234567)"
        ) is None

    def test_real_ticker_wins_over_legal_name_paren(self):
        assert extract_ticker(
            "Global Industries (UK) Ltd  (GIL)  (CIK 0001234567)"
        ) == "GIL"

    def test_live_edgar_shape_bvi(self):
        # Verbatim shape from EDGAR's live company list.
        assert extract_ticker(
            "New Century Logistics (BVI) Ltd  (NCEW)  (CIK 0001968043)"
        ) == "NCEW"

    def test_usa_paren_mid_name(self):
        assert extract_ticker(
            "Acme (USA) Holdings Inc  (CIK 0001234567)"
        ) is None

    def test_no_cik_group_uses_trailing_paren(self):
        # Defensive: EDGAR always appends a CIK group, but if absent the
        # trailing paren is still where a ticker annotation would live.
        assert extract_ticker("Acme (USA) Holdings Inc (ACME)") == "ACME"


class TestUpdatePipelineCompanyGuard:
    def test_company_not_erased_by_nameless_event(self):
        # A hit with cik but no display_names parses to company="" — it
        # must not blank out a name an earlier sweep already learned.
        pipeline = {}
        ev_named = SpinEvent(
            company="Versant Media Group, Inc.", cik="0002067876",
            ticker="VSNT", first_filed="2026-01-05", last_filed="2026-01-05",
            n_filings=1,
        )
        update_pipeline(pipeline, [ev_named], today="2026-06-01")
        ev_nameless = SpinEvent(
            company="", cik="0002067876", ticker=None,
            first_filed="2026-06-01", last_filed="2026-06-01", n_filings=1,
        )
        update_pipeline(pipeline, [ev_nameless], today="2026-07-03")
        assert pipeline["0002067876"]["company"] == "Versant Media Group, Inc."

    def test_new_entry_from_nameless_event_gets_empty_company(self):
        pipeline = {}
        ev = SpinEvent(
            company="", cik="0009999999", ticker=None,
            first_filed="2026-06-01", last_filed="2026-06-01", n_filings=1,
        )
        update_pipeline(pipeline, [ev], today="2026-07-03")
        assert pipeline["0009999999"]["company"] == ""
