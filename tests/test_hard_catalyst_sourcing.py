"""Hard-catalyst leg — pure-logic tests (2026-07-06, no network).

Form-enumeration of SC 13D from a daily index, the tradability split, the
Item-4-read flag, exclusion, and the strategic-review keyword supplement.
"""
from oracle import hard_catalyst_sourcing as hcs


_IDX = (
    "Form Type   Company                          CIK        Date Filed  File Name\n"
    "----------------------------------------------------------------------------\n"
    "SC 13D      TARGET OPERATING CO              1111111    2026-06-02  edgar/data/1111111/a.txt\n"
    "SC 13D/A    ESCALATION CO                    2222222    2026-06-03  edgar/data/2222222/b.txt\n"
    "SC 13G      PASSIVE INDEX HOLDER             3333333    2026-06-02  edgar/data/3333333/c.txt\n"
    "8-K         RANDOM CO                        4444444    2026-06-02  edgar/data/4444444/d.txt\n"
)


def test_enumerates_13d_only_and_flags_item4():
    out = hcs.sweep_by_form("2026-06-02", "2026-06-03",
                            cik_to_ticker={"0001111111": "TGT", "0002222222": "ESC"},
                            tradable_only=True, http_get=lambda url: _IDX)
    ciks = {c["cik"] for c in out}
    assert ciks == {"0001111111", "0002222222"}   # 13D + 13D/A; 13G & 8-K excluded
    for c in out:
        assert c["why_mispriced_type"] == "hard_catalyst"
        assert c["family"] == "activist_13d"
        assert c["requires_item4_read"] is True     # index can't see a campaign
        assert c["tradable"]


def test_tradability_filter_drops_unlisted():
    out = hcs.sweep_by_form("2026-06-02", "2026-06-03",
                            cik_to_ticker={"0001111111": "TGT"},  # only TGT listed
                            tradable_only=True, http_get=lambda url: _IDX)
    assert {c["cik"] for c in out} == {"0001111111"}


def test_keeps_unlisted_when_filter_off():
    out = hcs.sweep_by_form("2026-06-02", "2026-06-03", cik_to_ticker={},
                            tradable_only=False, http_get=lambda url: _IDX)
    assert len(out) == 2  # both 13D forms, none dropped
    assert all(not c["tradable"] for c in out)


def test_excludes_known_ciks():
    out = hcs.sweep_by_form("2026-06-02", "2026-06-03",
                            cik_to_ticker={"0001111111": "TGT", "0002222222": "ESC"},
                            exclude_ciks={"0001111111"},
                            tradable_only=True, http_get=lambda url: _IDX)
    assert {c["cik"] for c in out} == {"0002222222"}


def test_13g_is_never_enumerated():
    # SC 13G (passive) must not map to a catalyst family
    assert "SC 13G" not in hcs.CATALYST_FORM_TO_FAMILY
    assert "SC 13D" in hcs.CATALYST_FORM_TO_FAMILY


def test_strategic_review_supplement_tags_hard_catalyst():
    def fake(query, forms=None, date_from=None, date_to=None, offset=0):
        if offset:
            return {"hits": {"hits": [], "total": {"value": 1}}}
        return {"hits": {"hits": [
            {"_source": {"display_names": ["INPLAY CO (CIK 0000777777)"],
                         "file_date": "2026-06-05", "cik": "0000777777"}}],
            "total": {"value": 1}}}
    out = hcs.sweep_strategic_review("2026-06-01", "2026-06-30", search_fn=fake)
    assert len(out) == 1
    assert out[0]["why_mispriced_type"] == "hard_catalyst"
    assert out[0]["family"] == "strategic_review"
    assert out[0]["requires_item4_read"] is False
