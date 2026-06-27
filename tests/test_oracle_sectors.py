from oracle.sectors import SECTORS, normalize_sector, sector_breadth


def test_sectors_count():
    assert len(SECTORS) == 11


def test_normalize_technology():
    assert normalize_sector("Technology") == "technology"
    assert normalize_sector("Information Technology") == "technology"
    assert normalize_sector("Tech") == "technology"


def test_normalize_financials():
    assert normalize_sector("Financial Services") == "financials"
    assert normalize_sector("Banks") == "financials"


def test_normalize_real_estate():
    assert normalize_sector("Real Estate") == "real_estate"
    assert normalize_sector("REITs") == "real_estate"


def test_normalize_discretionary():
    assert normalize_sector("Consumer Discretionary") == "discretionary"
    assert normalize_sector("Consumer Cyclical") == "discretionary"


def test_normalize_unknown_passthrough():
    assert normalize_sector("Weird Stuff") == "weird_stuff"


def test_normalize_empty():
    assert normalize_sector("") == ""


def test_sector_breadth_all_positive():
    prices = {
        "tech": {"now": 110, "then": 100},
        "finance": {"now": 105, "then": 100},
    }
    assert sector_breadth(prices) == 1.0


def test_sector_breadth_half():
    prices = {
        "tech": {"now": 110, "then": 100},
        "finance": {"now": 90, "then": 100},
    }
    assert sector_breadth(prices) == 0.5


def test_sector_breadth_empty():
    assert sector_breadth({}) == 0.0


def test_sector_breadth_skips_invalid_prices():
    # Non-positive / missing price data has undefined momentum and is excluded
    # from both numerator and denominator — not counted as a flat/negative sector.
    prices = {
        "tech": {"now": 110, "then": 100},  # +10% -> positive, valid
        "neg":  {"now": -5, "then": 100},   # invalid -> skipped
        "zero": {"now": 50, "then": 0},     # invalid -> skipped
    }
    assert sector_breadth(prices) == 1.0  # 1 positive of 1 valid sector
    # All sectors invalid -> 0.0, and no sign-flip from a negative `then`.
    assert sector_breadth({"a": {"now": -1, "then": -2}}) == 0.0
