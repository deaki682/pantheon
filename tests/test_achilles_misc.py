"""Tests for journal, quotes, watchlist."""
import pytest

from achilles.journal import TradeEntry, append, per_class_stats, read, round_trip_pnl
from achilles.quotes import is_stale, normalize_quotes
from achilles.watchlist import SEED_WATCHLIST, WATCHLIST_CAP, attribute_source, build_watchlist


# ---- journal ----

def test_journal_append_and_read(tmp_path):
    p = tmp_path / "journal.jsonl"
    append(str(p), TradeEntry(
        timestamp="2024-05-29T10:00", event_id="e1", event_class="earnings_reaction",
        symbol="X", action="open", price=100, shares=2, dollars=200,
    ))
    append(str(p), TradeEntry(
        timestamp="2024-06-01T10:00", event_id="e1", event_class="earnings_reaction",
        symbol="X", action="close", price=110, shares=2, dollars=220, pnl=20,
    ))
    entries = read(str(p))
    assert len(entries) == 2


def test_round_trip_pnl(tmp_path):
    entries = [
        TradeEntry("2024-05-29", "e1", "earnings_reaction", "X", "open", 100, 2, 200),
        TradeEntry("2024-06-01", "e1", "earnings_reaction", "X", "close", 110, 2, 220),
    ]
    out = round_trip_pnl(entries)
    assert len(out) == 1
    assert out[0]["return_pct"] == pytest.approx(0.10)
    assert out[0]["hit"] is True


def test_per_class_stats():
    entries = [
        TradeEntry("a", "e1", "earnings_reaction", "X", "open", 100, 1, 100),
        TradeEntry("b", "e1", "earnings_reaction", "X", "close", 110, 1, 110),
        TradeEntry("c", "e2", "earnings_reaction", "Y", "open", 100, 1, 100),
        TradeEntry("d", "e2", "earnings_reaction", "Y", "close", 90, 1, 90),
        TradeEntry("e", "e3", "insider_cluster", "Z", "open", 100, 1, 100),
        TradeEntry("f", "e3", "insider_cluster", "Z", "close", 120, 1, 120),
    ]
    stats = per_class_stats(entries)
    assert stats["earnings_reaction"]["n"] == 2
    assert stats["earnings_reaction"]["hit_rate"] == 0.5
    assert stats["insider_cluster"]["hit_rate"] == 1.0


# ---- quotes ----

def test_normalize_quotes():
    rows = [
        {"symbol": "AAPL", "last_trade_price": "150.0"},
        {"symbol": "msft", "last_price": "350.0"},
        {"symbol": "BAD", "last_trade_price": "not-a-number"},
        {"symbol": "", "last_trade_price": "1.0"},
    ]
    out = normalize_quotes(rows)
    assert out == {"AAPL": 150.0, "MSFT": 350.0}


def test_is_stale_old():
    from datetime import datetime, timedelta
    ts = (datetime.utcnow() - timedelta(minutes=60)).isoformat()
    assert is_stale(ts, max_age_minutes=15)


def test_is_stale_fresh():
    from datetime import datetime
    ts = datetime.utcnow().isoformat()
    assert not is_stale(ts, max_age_minutes=15)


def test_is_stale_bad_input():
    assert is_stale("")
    assert is_stale("nonsense")


# ---- watchlist ----

def test_seed_watchlist_around_83():
    # The spec says "about 83" — allow a small wiggle room
    assert 70 <= len(SEED_WATCHLIST) <= 100


def test_watchlist_cap():
    assert WATCHLIST_CAP == 800


def test_build_watchlist_priority_order():
    wl = build_watchlist(
        activist_13d=["A", "B"],
        insider_clusters=["B", "C"],  # B is dup, skipped
        smart_money=["D"],
        seed=("E",),
    )
    assert wl[0] == "A"
    assert wl[1] == "B"
    assert wl[2] == "C"
    assert wl[3] == "D"
    assert wl[4] == "E"


def test_build_watchlist_dedup():
    wl = build_watchlist(activist_13d=["A", "a", "A"], seed=())
    assert wl == ["A"]


def test_build_watchlist_cap():
    long_list = [f"S{i}" for i in range(2000)]
    wl = build_watchlist(broad_screen=long_list, cap=100)
    assert len(wl) == 100


def test_build_watchlist_uses_seed():
    wl = build_watchlist()  # all sources empty -> falls back to seed
    assert len(wl) > 0
    assert wl[0] in SEED_WATCHLIST


def test_attribute_source():
    assert attribute_source(
        "AAPL", activist_13d=["AAPL"], insider_clusters=["MSFT"],
    ) == "activist_13d"


def test_attribute_source_priority():
    # AAPL in both — activist wins
    assert attribute_source(
        "AAPL", activist_13d=["AAPL"], insider_clusters=["AAPL"],
    ) == "activist_13d"


def test_attribute_source_unknown():
    assert attribute_source("UNKNOWN_TICKER", seed=()) == "unknown"
