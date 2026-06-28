import pytest

from achilles.events import (
    SPINOFF_POST_DAYS, SPINOFF_PRE_DAYS,
    aggregate_insider_clusters, build_event_for_filing,
    refine_guidance, refine_spinoff,
)
from shared.edgar import Filing
from shared.insiders import InsiderTxn


def _filing(form="8-K", items="2.02", symbol="ACME", acc="a-1"):
    return Filing(
        cik="1", accession_no=acc, form=form, filing_date="2024-05-29",
        primary_document="d.htm", items=items, symbol=symbol,
    )


def test_aggregate_insider_clusters_finds_qualifying():
    txns = [
        InsiderTxn("ACME", "Alice", "CEO", "P", "2024-05-29", 1500, 10, 15000.0),
        InsiderTxn("ACME", "Bob", "CFO", "P", "2024-05-30", 1500, 10, 15000.0),
    ]
    events = aggregate_insider_clusters(txns)
    assert len(events) == 1
    assert events[0].symbol == "ACME"
    assert events[0].event_class == "insider_cluster"


def test_aggregate_insider_skips_lonely():
    txns = [InsiderTxn("ACME", "Alice", "CEO", "P", "2024-05-29", 1500, 10, 15000.0)]
    events = aggregate_insider_clusters(txns)
    assert events == []


def test_aggregate_multi_symbol():
    txns = [
        InsiderTxn("ACME", "A", "", "P", "2024-05-29", 1500, 10, 15000.0),
        InsiderTxn("ACME", "B", "", "P", "2024-05-30", 1500, 10, 15000.0),
        InsiderTxn("WIDGET", "C", "", "P", "2024-05-29", 1500, 10, 15000.0),
        InsiderTxn("WIDGET", "D", "", "P", "2024-05-30", 1500, 10, 15000.0),
    ]
    events = aggregate_insider_clusters(txns)
    assert len(events) == 2
    assert {e.symbol for e in events} == {"ACME", "WIDGET"}


def test_refine_guidance_raised():
    f = _filing(items="7.01")
    body = "We are raising our full-year guidance"
    ev = refine_guidance(f, body)
    assert ev is not None
    assert ev.event_class == "guidance_revision"
    assert ev.metadata["direction"] == "raised"


def test_refine_guidance_reaffirmed_dropped():
    f = _filing(items="7.01")
    body = "We reaffirm our prior guidance"
    assert refine_guidance(f, body) is None


def test_refine_guidance_unknown_dropped():
    f = _filing(items="7.01")
    body = "Random text"
    assert refine_guidance(f, body) is None


def test_refine_spinoff_within_window():
    f = _filing(form="10-12B")
    body = "ex-date is June 5, 2024"
    ev = refine_spinoff(f, body, today="2024-05-30")
    # 6 days ahead, within +/- window
    assert ev is not None
    assert ev.metadata["ex_date"] == "2024-06-05"


def test_refine_spinoff_outside_window():
    f = _filing(form="10-12B")
    body = "ex-date is June 30, 2024"
    # 31 days ahead, outside the +7 pre-window
    assert refine_spinoff(f, body, today="2024-05-30") is None


def test_refine_spinoff_no_ex_date():
    f = _filing(form="10-12B")
    body = "no relevant dates"
    assert refine_spinoff(f, body, today="2024-05-30") is None


def test_build_event_for_filing_earnings():
    out = build_event_for_filing(_filing(items="2.02"))
    assert len(out) == 1
    assert out[0].event_class == "earnings_reaction"
    assert out[0].strength == 1.0  # no surprise_pct → neutral


def test_build_event_for_filing_earnings_with_surprise():
    out = build_event_for_filing(_filing(items="2.02"), surprise_pct=15.0)
    assert len(out) == 1
    assert out[0].event_class == "earnings_reaction"
    assert 0.95 <= out[0].strength <= 1.0  # sweet spot
    assert out[0].metadata["surprise_pct"] == 15.0


def test_build_event_for_filing_earnings_extreme_surprise_not_penalized():
    out = build_event_for_filing(_filing(items="2.02"), surprise_pct=150.0)
    assert len(out) == 1
    assert out[0].strength >= 0.85  # small-cap extreme beats are valid


def test_build_event_for_filing_13d():
    out = build_event_for_filing(_filing(form="SC 13D", items=""))
    assert len(out) == 1
    assert out[0].event_class == "activist_13d"


def test_build_event_for_filing_ma():
    out = build_event_for_filing(_filing(items="2.01"))
    assert len(out) == 1
    assert out[0].event_class == "ma_target"


def test_build_event_for_filing_guidance_needs_body():
    f = _filing(items="7.01")
    # No body -> guidance can't be classified
    out = build_event_for_filing(f, body_text="", today="2024-05-29")
    assert out == []
    # With body -> works
    out = build_event_for_filing(f, body_text="raising guidance to $5", today="2024-05-29")
    assert len(out) == 1
    assert out[0].event_class == "guidance_revision"


def test_constants():
    assert SPINOFF_PRE_DAYS == 7
    assert SPINOFF_POST_DAYS == 21
