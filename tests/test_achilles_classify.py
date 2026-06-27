import pytest

from achilles.classify import EVENT_CLASSES, classify_filing, is_amendment
from shared.edgar import Filing


def _f(form, items="", symbol="ACME"):
    return Filing(
        cik="1", accession_no="a-1", form=form, filing_date="2024-05-29",
        primary_document="d.htm", items=items, symbol=symbol,
    )


def test_six_event_classes():
    assert len(EVENT_CLASSES) == 6


def test_classify_8k_earnings():
    out = classify_filing(_f("8-K", "2.02"))
    assert "earnings_reaction" in out


def test_classify_8k_ma_target():
    out = classify_filing(_f("8-K", "2.01"))
    assert "ma_target" in out


def test_classify_8k_guidance():
    out = classify_filing(_f("8-K", "7.01"))
    assert "guidance_revision" in out


def test_classify_8k_unknown_item():
    out = classify_filing(_f("8-K", "5.02"))
    assert out == []


def test_classify_form4_is_candidate():
    out = classify_filing(_f("4"))
    assert out == ["insider_cluster_candidate"]


def test_classify_13d_fresh():
    out = classify_filing(_f("SC 13D"))
    assert out == ["activist_13d"]


def test_classify_13d_amendment_excluded():
    out = classify_filing(_f("SC 13D/A"))
    assert out == []


def test_classify_spinoff_form():
    out = classify_filing(_f("10-12B"))
    assert out == ["spinoff_window_candidate"]


def test_classify_unknown_form():
    out = classify_filing(_f("10-Q"))
    assert out == []


def test_is_amendment():
    assert is_amendment("SC 13D/A")
    assert not is_amendment("SC 13D")
    assert not is_amendment("8-K")
