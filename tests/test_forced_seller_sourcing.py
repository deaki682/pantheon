"""Forced-seller event sourcing — the coverage spine (2026-07-06).

Pure-logic tests (no network): the family registry integrity, graveyard
exclusion, the paged parse, and the cross-family dedupe/merge in `sweep`.
"""
from oracle import forced_seller_sourcing as fss


def _payload(*rows):
    """Build an EDGAR-FTS-shaped payload from (company, cik, date) rows."""
    hits = [
        {"_source": {"display_names": [f"{co} (CIK {cik})"], "file_date": d, "cik": cik}}
        for (co, cik, d) in rows
    ]
    return {"hits": {"hits": hits, "total": {"value": len(hits)}}}


def test_live_families_are_never_graveyard():
    for fam in fss.LIVE_FAMILIES:
        assert not fss.is_graveyard(fam.key), f"{fam.key} is live AND graveyard"


def test_graveyard_and_hermes_are_flagged():
    assert fss.is_graveyard("spinoff_orphans")
    assert fss.is_graveyard("cef_tender_convergence")
    assert fss.is_graveyard("ipo_lockup_reversion")
    assert fss.is_graveyard("sp500_index_addition")
    assert fss.is_graveyard(fss.HERMES_DOMAIN_KEY)      # merger targets = Hermes
    assert not fss.is_graveyard("post_bk_emergence")     # live
    assert not fss.is_graveyard("fund_liquidation")      # live


def test_every_live_family_states_its_mechanism():
    # G2: a channel with no named forced counterparty is not sourceable
    for fam in fss.LIVE_FAMILIES:
        assert len(fam.mechanism) >= 30, f"{fam.key} lacks a real mechanism"


def test_search_family_parses_injected_payload():
    fam = fss.family_by_key("post_bk_emergence")
    def fake(query, forms=None, date_from=None, date_to=None, offset=0):
        if offset:
            return {"hits": {"hits": [], "total": {"value": 1}}}
        return _payload(("REORG CO", "0000111111", "2026-06-10"))
    cands = fss.search_family(fam, "2026-06-01", "2026-06-30", search_fn=fake)
    assert len(cands) == 1
    assert cands[0]["cik"] == "0000111111"
    assert cands[0]["family"] == "post_bk_emergence"
    assert cands[0]["mechanism"]  # carried through


def test_sweep_dedupes_and_merges_family_tags():
    # same CIK surfaces in two channels → one candidate, both tags, ranked first
    def fake(query, forms=None, date_from=None, date_to=None, offset=0):
        if offset:
            return {"hits": {"hits": [], "total": {"value": 1}}}
        if query == fss.family_by_key("post_bk_emergence").query:
            return _payload(("MULTI CO", "0000222222", "2026-06-05"))
        if query == fss.family_by_key("rights_offering").query:
            return _payload(("MULTI CO", "0000222222", "2026-06-08"),
                            ("SOLO CO", "0000333333", "2026-06-09"))
        return {"hits": {"hits": [], "total": {"value": 0}}}
    fams = (fss.family_by_key("post_bk_emergence"), fss.family_by_key("rights_offering"))
    out = fss.sweep("2026-06-01", "2026-06-30", families=fams, search_fn=fake)
    ciks = [c["cik"] for c in out]
    assert "0000222222" in ciks and "0000333333" in ciks
    multi = next(c for c in out if c["cik"] == "0000222222")
    assert set(multi["families"]) == {"post_bk_emergence", "rights_offering"}
    assert out[0]["cik"] == "0000222222"  # multi-channel name ranked first


def test_sweep_refuses_graveyard_family_even_if_passed():
    bad = fss.Family(key="spinoff_orphans", label="dead", query="x", forms=("8-K",),
                     mechanism="a refuted family that must never be sourced again")
    def fake(query, forms=None, date_from=None, date_to=None, offset=0):
        return _payload(("SHOULD NOT APPEAR", "0000444444", "2026-06-01"))
    out = fss.sweep("2026-06-01", "2026-06-30", families=(bad,), search_fn=fake)
    assert out == [], "a graveyard family leaked candidates into the sweep"


def test_sweep_excludes_known_ciks():
    def fake(query, forms=None, date_from=None, date_to=None, offset=0):
        if offset:
            return {"hits": {"hits": [], "total": {"value": 1}}}
        return _payload(("KNOWN", "0000555555", "2026-06-01"))
    fams = (fss.family_by_key("post_bk_emergence"),)
    out = fss.sweep("2026-06-01", "2026-06-30", families=fams,
                    exclude_ciks={"0000555555"}, search_fn=fake)
    assert out == []


# --- form-enumeration path (the measured Stage-1 upgrade) ---

_FAKE_IDX = (
    "Form Type        Company                                       CIK        Date Filed  File Name\n"
    "-----------------------------------------------------------------------------------------------\n"
    "SC TO-I          JAPAN SMALLER CAPITALIZATION FUND INC          859796     2026-06-01  edgar/data/859796/x.txt\n"
    "SC TO-I          Blackstone Private Credit Fund                 1803498    2026-06-01  edgar/data/1803498/y.txt\n"
    "N-8F             Some Winddown Fund LLC                         1234567    2026-06-01  edgar/data/1234567/z.txt\n"
    "8-K              Random Operating Co                            9999999    2026-06-01  edgar/data/9999999/a.txt\n"
)


def test_enumerate_by_form_parses_daily_index():
    got = fss.enumerate_by_form("2026-06-01", "2026-06-01", ["SC TO-I", "N-8F"],
                                http_get=lambda url: _FAKE_IDX)
    assert set(got) == {"0000859796", "0001803498", "0001234567"}  # 8-K excluded
    assert got["0000859796"]["forms"] == {"SC TO-I"}
    assert got["0000859796"]["name"].startswith("JAPAN SMALLER")


def test_sweep_by_form_tradability_filter_drops_nontraded():
    # only JOF is in the listed-ticker map; the private funds are not
    out = fss.sweep_by_form("2026-06-01", "2026-06-01",
                            cik_to_ticker={"0000859796": "JOF"},
                            tradable_only=True, http_get=lambda url: _FAKE_IDX)
    assert {c["cik"] for c in out} == {"0000859796"}
    jof = out[0]
    assert jof["ticker"] == "JOF" and jof["family"] == "odd_lot_tender" and jof["tradable"]


def test_sweep_by_form_keeps_all_when_filter_off():
    out = fss.sweep_by_form("2026-06-01", "2026-06-01", cik_to_ticker={},
                            tradable_only=False, http_get=lambda url: _FAKE_IDX)
    assert len(out) == 3  # SC TO-I x2 + N-8F, all enumerated; 8-K is not a mapped form


def test_delisting_demoted_not_form_enumerated():
    # DEMOTED 2026-07-06: Form 25 measured as ~all security-level/distress noise;
    # the real index-deletion mechanic is an index-provider announcement, not EDGAR.
    assert "25-NSE" not in fss.FORM_TO_FAMILY
    assert "25" not in fss.FORM_TO_FAMILY
    assert "delisting" not in set(fss.FORM_TO_FAMILY.values())
    assert fss.FORM_TO_FAMILY["N-8F ORDR"] == "fund_liquidation"  # real form string, not bare N-8F


def test_delisting_form_no_longer_enumerated():
    # a 25-NSE line must NOT produce a candidate (channel demoted); the tender does
    idx = ("25-NSE           SOME DELISTED CO                              4242424    2026-06-01  edgar/data/x.txt\n"
           "SC TO-I          A TENDER FUND                                 5252525    2026-06-01  edgar/data/y.txt\n")
    out = fss.sweep_by_form("2026-06-01", "2026-06-01", cik_to_ticker={"0004242424": "DLST", "0005252525": "TND"},
                            tradable_only=True, http_get=lambda url: idx)
    ciks = {c["cik"] for c in out}
    assert "0004242424" not in ciks           # delisting demoted
    assert ciks == {"0005252525"}             # only the tender survives
