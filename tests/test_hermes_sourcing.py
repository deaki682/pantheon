"""Network-free tests for Hermes's announced-deal enumerator. The parser must
recover EVERY announced-deal target from the daily-index text (the complete
population) and, critically, must NOT confuse a regular annual proxy ('DEF 14A',
with the space) for a merger proxy ('DEFM14A') — a false include pollutes the
deal universe; a false exclude silently drops a tradable deal."""
from hermes.sourcing import (
    DEAL_FORMS,
    DealCandidate,
    finalize,
    new_candidates,
    parse_index_text,
)

# A realistic EDGAR daily form.idx slice: two real deals (one filing twice), a
# tender offer, and two NON-deals that must be excluded (a regular annual proxy
# and a 10-K).
INDEX_DAY1 = (
    "Form Type    Company Name                                          CIK         Date Filed  File Name\n"
    "-------------------------------------------------------------------------------------------------\n"
    "PREM14A         Alpha Target Inc                                   1234567     2026-06-10  edgar/data/1234567/a.htm\n"
    "DEF 14A         Boring Annual Co                                   9999999     2026-06-10  edgar/data/9999999/b.htm\n"
    "10-K            Some Filer LLC                                     8888888     2026-06-10  edgar/data/8888888/c.htm\n"
)
INDEX_DAY2 = (
    "DEFM14A         Alpha Target Inc                                   1234567     2026-06-20  edgar/data/1234567/d.htm\n"
    "SC 14D9         Beta Corp                                          7654321     2026-06-20  edgar/data/7654321/e.htm\n"
)
INDEX_DAY3 = (
    "DEFM14A/A       Alpha Target Inc                                   1234567     2026-06-21  edgar/data/1234567/f.htm\n"
)


def _acc():
    acc = {}
    parse_index_text(INDEX_DAY1, "2026-06-10", acc)
    parse_index_text(INDEX_DAY2, "2026-06-20", acc)
    parse_index_text(INDEX_DAY3, "2026-06-21", acc)   # Alpha amends → freshest
    return acc


def test_excludes_regular_proxy_and_non_deals():
    acc = _acc()
    # only the two real TARGETS, keyed by CIK; DEF 14A and 10-K are gone
    assert set(acc.keys()) == {"0001234567", "0007654321"}


def test_groups_by_cik_across_forms_and_amendments():
    acc = _acc()
    alpha = acc["0001234567"]
    # PREM14A + DEFM14A + the /A amendment all fold into ONE target
    assert alpha["forms"] == {"PREM14A", "DEFM14A"}
    assert alpha["n"] == 3                      # three filings, one deal


def test_finalize_backfills_ticker_and_sorts_fresh_first():
    cands = finalize(_acc(), cik_to_symbol={"0001234567": "ALPH"})
    assert all(isinstance(c, DealCandidate) for c in cands)
    assert all(c.requires_read for c in cands)  # never funded on the form alone
    by_cik = {c.cik: c for c in cands}
    assert by_cik["0001234567"].symbol == "ALPH"
    assert by_cik["0007654321"].symbol is None  # unknown ticker → left for the read
    # channels are human-readable labels drawn from DEAL_FORMS
    assert set(by_cik["0001234567"].channels) == {
        DEAL_FORMS["PREM14A"], DEAL_FORMS["DEFM14A"]}
    # freshest last_filed first: Alpha (amended 06-21) before Beta (06-20)
    assert cands[0].cik == "0001234567"


def test_new_candidates_drops_tracked():
    cands = finalize(_acc())
    fresh = new_candidates(cands, tracked_ciks=["1234567"])  # raw CIK normalizes
    assert [c.cik for c in fresh] == ["0007654321"]


def test_empty_index_is_empty():
    assert finalize(parse_index_text("", "2026-06-10", {})) == []
