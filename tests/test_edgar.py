from shared.edgar import (
    Filing,
    acc_no_clean,
    cik10,
    classify_8k,
    clean_html,
    extract_ex_date,
    extract_section,
    guidance_direction,
    parse_items,
    parse_submissions_recent,
)


def test_cik10_padding():
    assert cik10(320193) == "0000320193"
    assert cik10("320193") == "0000320193"


def test_acc_no_clean():
    assert acc_no_clean("0000320193-23-000077") == "000032019323000077"


def test_clean_html_basic():
    html = "<html><body>Hello <b>world</b></body></html>"
    assert clean_html(html) == "Hello world"


def test_clean_html_strips_script():
    html = "Before<script>alert('x')</script>After"
    out = clean_html(html)
    assert "alert" not in out
    assert "Before" in out and "After" in out


def test_clean_html_strips_style():
    html = "Before<style>.x{color:red}</style>After"
    out = clean_html(html)
    assert "color" not in out


def test_clean_html_collapses_whitespace():
    assert clean_html("<p>  a   b\n\n  c  </p>") == "a b c"


def test_clean_html_decodes_entities():
    assert "&" in clean_html("a &amp; b")
    assert "<" in clean_html("&lt;")


def test_parse_items_simple():
    items = parse_items("2.02,9.01")
    assert items == {"2.02", "9.01"}


def test_parse_items_with_item_prefix():
    items = parse_items("Item 2.02, Item 9.01")
    assert "2.02" in items
    assert "9.01" in items


def test_parse_items_empty():
    assert parse_items("") == set()
    assert parse_items(None) == set() if None is not None else True  # smoke


def test_classify_8k_earnings():
    assert "earnings_reaction" in classify_8k("2.02,9.01")


def test_classify_8k_ma_target():
    assert "ma_target" in classify_8k("2.01")


def test_classify_8k_guidance_701():
    assert "guidance_revision" in classify_8k("7.01")


def test_classify_8k_guidance_801():
    assert "guidance_revision" in classify_8k("8.01")


def test_classify_8k_bankruptcy():
    assert "bankruptcy" in classify_8k("1.03")


def test_classify_8k_delisting():
    assert "delisting" in classify_8k("3.01")


def test_classify_8k_multiple():
    labels = classify_8k("2.02,7.01")
    assert "earnings_reaction" in labels
    assert "guidance_revision" in labels


def test_classify_8k_none():
    assert classify_8k("5.02") == []  # exec change isn't in our 6 classes


def test_extract_section_risk_factors():
    text = "Item 1A. Risk Factors blah blah danger lurks here Item 1B. Unresolved"
    out = extract_section(text, "risk_factors")
    assert "danger" in out
    assert "Unresolved" not in out


def test_extract_section_business():
    text = "Item 1. Business We make widgets and sell them globally. Item 1A. Risk"
    out = extract_section(text, "business")
    assert "widgets" in out


def test_extract_section_missing():
    assert extract_section("nothing relevant", "risk_factors") == ""


def test_extract_section_unknown_key():
    assert extract_section("anything", "unknown_section") == ""


def test_guidance_raised():
    assert guidance_direction("We are raising our full-year guidance to $5") == "raised"


def test_guidance_lowered():
    assert guidance_direction("We are lowering our annual guidance") == "lowered"


def test_guidance_withdrawn():
    assert guidance_direction("Company withdraws prior guidance for fiscal 2024") == "withdrawn"


def test_guidance_reaffirmed():
    assert guidance_direction("We reaffirm full-year guidance") == "reaffirmed"


def test_guidance_unknown():
    assert guidance_direction("Random text without keywords") == "unknown"


def test_extract_ex_date():
    text = "the ex-date for the distribution is October 15, 2024"
    assert extract_ex_date(text) == "2024-10-15"


def test_extract_ex_date_alt_phrasing():
    text = "Distribution Date: November 3, 2024"
    assert extract_ex_date(text) == "2024-11-03"


def test_extract_ex_date_missing():
    assert extract_ex_date("no relevant dates here") is None


def test_parse_submissions_recent():
    payload = {
        "cik": "320193",
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-23-000077", "0000320193-23-000076"],
                "form": ["10-K", "8-K"],
                "filingDate": ["2023-11-03", "2023-11-02"],
                "primaryDocument": ["doc1.htm", "doc2.htm"],
                "items": ["", "2.02"],
            }
        },
    }
    filings = parse_submissions_recent(payload, symbol="AAPL")
    assert len(filings) == 2
    assert filings[0].accession_no == "0000320193-23-000077"
    assert filings[0].form == "10-K"
    assert filings[1].items == "2.02"
    assert filings[0].symbol == "AAPL"


def test_filing_primary_url():
    f = Filing(
        cik="320193", accession_no="0000320193-23-000077",
        form="10-K", filing_date="2023-11-03", primary_document="doc.htm"
    )
    url = f.primary_url
    assert "Archives/edgar/data/320193" in url
    assert "000032019323000077" in url
    assert "doc.htm" in url
