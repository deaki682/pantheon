from datetime import date

from catalyst.calendar import (
    build_calendar,
    make_event,
    next_week_window,
    normalize_earnings,
)

TODAY = date(2026, 7, 1)


class TestWindow:
    def test_seven_day_window(self):
        start, end = next_week_window(TODAY)
        assert start == TODAY
        assert (end - start).days == 7


class TestMakeEvent:
    def test_days_until_and_schema(self):
        ev = make_event(
            ticker="xyz", event_type="earnings", event_date="2026-07-03",
            timing="am", is_binary=True, source="test", today=TODAY,
        )
        assert ev["ticker"] == "XYZ"
        assert ev["days_until"] == 2
        assert ev["is_binary"] is True
        assert ev["expected_priced_move_pct"] is None  # filled later
        assert ev["event_type"] == "earnings"

    def test_unknown_type_coerced(self):
        ev = make_event(ticker="A", event_type="martian_invasion",
                        event_date="2026-07-02", today=TODAY)
        assert ev["event_type"] == "other"

    def test_bad_date_is_none(self):
        ev = make_event(ticker="A", event_type="econ", event_date="not-a-date", today=TODAY)
        assert ev["event_date"] is None
        assert ev["days_until"] is None


class TestNormalizeEarnings:
    def _row(self, sym, d, est="1.00", actual=None, verified=True, timing="am"):
        return {"symbol": sym, "eps": {"estimate": est, "actual": actual},
                "report": {"date": d, "timing": timing, "verified": verified}}

    def test_basic(self):
        out = normalize_earnings([self._row("GIS", "2026-07-01")], today=TODAY)
        assert len(out) == 1
        assert out[0]["ticker"] == "GIS"
        assert out[0]["is_binary"] is True
        assert out[0]["consensus"]["eps_est"] == 1.0
        assert out[0]["confidence"] == 0.9

    def test_skips_already_reported(self):
        out = normalize_earnings([self._row("X", "2026-07-01", actual="1.10")], today=TODAY)
        assert out == []

    def test_dedups(self):
        rows = [self._row("PRPH", "2026-07-01"), self._row("PRPH", "2026-07-01")]
        assert len(normalize_earnings(rows, today=TODAY)) == 1

    def test_unverified_downweighted(self):
        out = normalize_earnings([self._row("Q", "2026-07-06", verified=False)], today=TODAY)
        assert out[0]["confidence"] == 0.5

    def test_missing_fields_skipped(self):
        out = normalize_earnings([{"symbol": "", "report": {}}, {"report": {"date": "2026-07-02"}}], today=TODAY)
        assert out == []


class TestBuildCalendar:
    def test_sorted_by_days_then_confidence(self):
        a = make_event(ticker="FAR", event_type="earnings", event_date="2026-07-07", confidence=0.9, today=TODAY)
        b = make_event(ticker="SOON", event_type="earnings", event_date="2026-07-02", confidence=0.5, today=TODAY)
        c = make_event(ticker="SOONER", event_type="earnings", event_date="2026-07-02", confidence=0.9, today=TODAY)
        cal = build_calendar([a, b, c])
        assert [e["ticker"] for e in cal] == ["SOONER", "SOON", "FAR"]

    def test_clips_to_window(self):
        start, end = next_week_window(TODAY)
        inside = make_event(ticker="IN", event_type="econ", event_date="2026-07-03", today=TODAY)
        outside = make_event(ticker="OUT", event_type="econ", event_date="2026-08-15", today=TODAY)
        cal = build_calendar([inside, outside], start=start, end=end)
        assert [e["ticker"] for e in cal] == ["IN"]
