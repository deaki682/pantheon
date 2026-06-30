import pytest

from midas.prescan import (
    compute_volume_anomalies,
    form4_fts_to_clusters,
    merge_insider_clusters,
    parse_finviz_short_text,
)


class TestForm4FtsToClusters:
    def test_basic_cluster(self):
        fts = {
            "ACME": [
                {"filer": "Alice", "filing_date": "2026-06-28", "accession": "a1"},
                {"filer": "Bob", "filing_date": "2026-06-29", "accession": "a2"},
            ]
        }
        clusters = form4_fts_to_clusters(fts)
        assert "ACME" in clusters
        assert clusters["ACME"]["insider_count"] == 2
        assert clusters["ACME"]["latest_date"] == "2026-06-29"

    def test_single_filer_excluded(self):
        fts = {
            "SOLO": [
                {"filer": "Alice", "filing_date": "2026-06-28", "accession": "a1"},
                {"filer": "Alice", "filing_date": "2026-06-29", "accession": "a2"},
            ]
        }
        clusters = form4_fts_to_clusters(fts)
        assert "SOLO" not in clusters

    def test_empty_input(self):
        assert form4_fts_to_clusters({}) == {}

    def test_custom_min_filers(self):
        fts = {
            "ACME": [
                {"filer": "A", "filing_date": "2026-06-28", "accession": "a1"},
                {"filer": "B", "filing_date": "2026-06-29", "accession": "a2"},
            ]
        }
        assert "ACME" in form4_fts_to_clusters(fts, min_filers=2)
        assert "ACME" not in form4_fts_to_clusters(fts, min_filers=3)

    def test_filing_count_includes_all(self):
        fts = {
            "ACME": [
                {"filer": "A", "filing_date": "2026-06-27", "accession": "a1"},
                {"filer": "A", "filing_date": "2026-06-28", "accession": "a2"},
                {"filer": "B", "filing_date": "2026-06-29", "accession": "a3"},
            ]
        }
        clusters = form4_fts_to_clusters(fts)
        assert clusters["ACME"]["filing_count"] == 3
        assert clusters["ACME"]["insider_count"] == 2


class TestMergeInsiderClusters:
    def test_fresh_overrides_stale(self):
        oracle = {"ACME": {"insider_count": 2, "latest_date": "2026-04-15"}}
        fresh = {"ACME": {"insider_count": 4, "latest_date": "2026-06-28"}}
        merged = merge_insider_clusters(oracle, fresh)
        assert merged["ACME"]["insider_count"] == 4

    def test_preserves_oracle_only(self):
        oracle = {"OLD": {"insider_count": 3}}
        fresh = {"NEW": {"insider_count": 2}}
        merged = merge_insider_clusters(oracle, fresh)
        assert "OLD" in merged
        assert "NEW" in merged

    def test_case_normalization(self):
        oracle = {"acme": {"insider_count": 2}}
        fresh = {"Acme": {"insider_count": 3}}
        merged = merge_insider_clusters(oracle, fresh)
        assert "ACME" in merged
        assert merged["ACME"]["insider_count"] == 3

    def test_empty_both(self):
        assert merge_insider_clusters({}, {}) == {}


class TestComputeVolumeAnomalies:
    def test_detects_high_volume(self):
        bars = [{"volume": 100}] * 25 + [{"volume": 300}] * 5
        anomalies = compute_volume_anomalies({"ACME": bars})
        assert "ACME" in anomalies
        assert anomalies["ACME"] == pytest.approx(3.0)

    def test_normal_volume_excluded(self):
        bars = [{"volume": 100}] * 30
        anomalies = compute_volume_anomalies({"ACME": bars})
        assert anomalies.get("ACME", 1.0) <= 1.0

    def test_insufficient_data(self):
        bars = [{"volume": 100}] * 5
        anomalies = compute_volume_anomalies({"ACME": bars})
        assert "ACME" not in anomalies

    def test_zero_baseline_excluded(self):
        bars = [{"volume": 0}] * 25 + [{"volume": 100}] * 5
        anomalies = compute_volume_anomalies({"ACME": bars})
        assert "ACME" not in anomalies

    def test_multiple_symbols(self):
        high = [{"volume": 100}] * 25 + [{"volume": 500}] * 5
        low = [{"volume": 100}] * 30
        anomalies = compute_volume_anomalies({"HOT": high, "COLD": low})
        assert "HOT" in anomalies
        assert anomalies["HOT"] == pytest.approx(5.0)


class TestParseFinvizShortText:
    def test_labeled_format(self):
        text = "ACME: Short Float 45.20% | Short Ratio 3.5"
        result = parse_finviz_short_text(text)
        assert result["ACME"] == pytest.approx(45.20)

    def test_compact_format(self):
        text = "XYZ: 30.50%"
        result = parse_finviz_short_text(text)
        assert result["XYZ"] == pytest.approx(30.50)

    def test_spaced_format(self):
        text = "FOO  25.00%"
        result = parse_finviz_short_text(text)
        assert result["FOO"] == pytest.approx(25.0)

    def test_below_minimum_excluded(self):
        text = "LOW: Short Float 10.00%"
        result = parse_finviz_short_text(text)
        assert "LOW" not in result

    def test_multiple_lines(self):
        text = "ACME: Short Float 45.20%\nXYZ: Short Float 30.00%\nLOW: 5.00%"
        result = parse_finviz_short_text(text)
        assert len(result) == 2
        assert "ACME" in result
        assert "XYZ" in result
        assert "LOW" not in result

    def test_empty_input(self):
        assert parse_finviz_short_text("") == {}

    def test_no_matching_lines(self):
        text = "No data available\nPlease try again later"
        assert parse_finviz_short_text(text) == {}
