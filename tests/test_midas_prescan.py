import pytest

from midas.prescan import (
    compute_volume_anomalies,
    filter_stale_earnings_signals,
    find_reaction_bar,
    form4_fts_to_clusters,
    merge_insider_clusters,
    parse_finviz_short_text,
)


def _bar(close, volume=100):
    return {"close_price": str(close), "volume": volume, "begins_at": "2026-06-01T00:00:00Z"}


def _series(closes, *, volumes=None):
    """Build oldest-first daily bars from a list of closes."""
    vols = volumes or [100] * len(closes)
    return [
        {"close_price": str(c), "volume": v, "begins_at": f"2026-06-{i+1:02d}T00:00:00Z"}
        for i, (c, v) in enumerate(zip(closes, vols))
    ]


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


class TestFindReactionBar:
    def test_finds_gap_up_on_volume(self):
        # flat ~20 days, then a +8% gap on 3x volume, then flat for 2 more days
        closes = [100.0] * 20 + [108.0, 108.5, 108.2]
        vols = [100] * 20 + [300, 120, 110]
        rb = find_reaction_bar(_series(closes, volumes=vols))
        assert rb is not None
        assert rb["gap"] > 0.05
        assert rb["age_days"] == 2  # two bars after the reaction

    def test_no_reaction_when_flat(self):
        rb = find_reaction_bar(_series([100.0] * 25))
        assert rb is None

    def test_small_move_ignored(self):
        # 2% wiggle never clears the 4% gap floor
        closes = [100.0, 102.0] * 12
        assert find_reaction_bar(_series(closes)) is None

    def test_requires_volume_when_baseline_present(self):
        # 8% gap but on NORMAL volume -> not a real reaction
        closes = [100.0] * 20 + [108.0]
        vols = [100] * 21
        assert find_reaction_bar(_series(closes, volumes=vols)) is None

    def test_empty_and_short(self):
        assert find_reaction_bar([]) is None
        assert find_reaction_bar(_series([100.0])) is None

    def test_picks_most_significant(self):
        # two reactions: older +6%/2x, recent +10%/4x -> pick the bigger
        closes = [100.0] * 10 + [106.0] + [106.0] * 5 + [116.6]
        vols = [100] * 10 + [200] + [100] * 5 + [400]
        rb = find_reaction_bar(_series(closes, volumes=vols))
        assert rb["gap"] > 0.08
        assert rb["age_days"] == 0


class TestFilterStaleEarningsSignals:
    def test_drops_old_reaction(self):
        # reaction 6 bars ago -> beyond the 3-day window -> dropped
        closes = [50.0] * 15 + [56.0] + [56.0] * 6
        vols = [100] * 15 + [400] + [100] * 6
        hist = {"DAKT": _series(closes, volumes=vols)}
        earn, guid, dropped = filter_stale_earnings_signals(
            {"DAKT": {"is_beat": True}}, set(), hist
        )
        assert "DAKT" not in earn
        assert "DAKT" in dropped

    def test_keeps_fresh_reaction(self):
        # reaction on the latest bar (age 0), +12% move stays under STALENESS_PCT
        closes = [50.0] * 20 + [56.0]
        vols = [100] * 20 + [400]
        hist = {"FRSH": _series(closes, volumes=vols)}
        earn, guid, dropped = filter_stale_earnings_signals(
            {"FRSH": {"is_beat": True}}, set(), hist
        )
        assert "FRSH" in earn
        assert not dropped

    def test_drops_fresh_but_already_ran(self):
        # reaction is recent (age 0) but a +25% gap has already priced it in
        closes = [50.0] * 20 + [62.5]
        vols = [100] * 20 + [400]
        hist = {"RAN": _series(closes, volumes=vols)}
        earn, guid, dropped = filter_stale_earnings_signals(
            {"RAN": {"is_beat": True}}, set(), hist
        )
        assert "RAN" not in earn
        assert "moved" in dropped["RAN"]

    def test_keeps_undigested_beat(self):
        # beat with no reaction on the tape yet -> the ideal pre-drift setup
        hist = {"WAIT": _series([100.0] * 25)}
        earn, guid, dropped = filter_stale_earnings_signals(
            {"WAIT": {"is_beat": True}}, set(), hist
        )
        assert "WAIT" in earn

    def test_keeps_when_no_historicals(self):
        earn, guid, dropped = filter_stale_earnings_signals(
            {"NODATA": {"is_beat": True}}, set(), {}
        )
        assert "NODATA" in earn  # don't over-filter without a tape

    def test_filters_guidance_too(self):
        closes = [30.0] * 15 + [34.0] + [34.0] * 6
        vols = [100] * 15 + [400] + [100] * 6
        hist = {"OLDG": _series(closes, volumes=vols)}
        earn, guid, dropped = filter_stale_earnings_signals({}, {"OLDG"}, hist)
        assert "OLDG" not in guid
        assert "OLDG" in dropped

    def test_none_inputs(self):
        earn, guid, dropped = filter_stale_earnings_signals(None, None, {})
        assert earn == {}
        assert guid == set()
        assert dropped == {}
