from shared.insiders import InsiderTxn, cluster_signal, parse_form4, scan_universe


_F4 = """<?xml version="1.0"?>
<ownershipDocument>
  <issuer>
    <issuerTradingSymbol>ACME</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>John Doe</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>1</isDirector>
      <officerTitle>CEO</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <transactionDate><value>2024-05-30</value></transactionDate>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
        <transactionPricePerShare><value>15.50</value></transactionPricePerShare>
      </transactionAmounts>
      <transactionCoding>
        <transactionCode>P</transactionCode>
      </transactionCoding>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""


def test_parse_form4_basic():
    txns = parse_form4(_F4, accession_no="acc-1")
    assert len(txns) == 1
    t = txns[0]
    assert t.symbol == "ACME"
    assert t.insider_name == "John Doe"
    assert "CEO" in t.insider_title
    assert t.transaction_code == "P"
    assert t.shares == 1000
    assert t.price == 15.5
    assert t.dollars == pytest.approx(15500.0)
    assert t.is_open_market_buy


def test_parse_form4_empty():
    assert parse_form4("") == []
    assert parse_form4("not xml") == []


def test_parse_form4_no_transactions():
    xml = "<ownershipDocument><issuer><issuerTradingSymbol>X</issuerTradingSymbol></issuer></ownershipDocument>"
    assert parse_form4(xml) == []


def test_cluster_signal_below_threshold():
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 100, 5.0, 500.0),
    ]
    assert cluster_signal(txns) is None


def test_cluster_signal_one_insider():
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 2000, 10.0, 20000.0),
    ]
    assert cluster_signal(txns) is None  # only 1 insider


def test_cluster_signal_two_insiders():
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 2000, 10.0, 20000.0),
        InsiderTxn("X", "Bob", "CFO", "P", "2024-05-30", 1500, 10.0, 15000.0),
    ]
    sig = cluster_signal(txns)
    assert sig is not None
    assert sig["symbol"] == "X"
    assert sig["insider_count"] == 2
    assert "Alice" in sig["insiders"]
    assert "Bob" in sig["insiders"]


def test_cluster_signal_below_min_dollars():
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 50, 10.0, 500.0),
        InsiderTxn("X", "Bob", "CFO", "P", "2024-05-30", 50, 10.0, 500.0),
    ]
    # Each below $10k threshold
    assert cluster_signal(txns) is None


def test_cluster_signal_aggregates_per_insider():
    # Alice has two smaller buys that aggregate above the threshold
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 500, 10.0, 5000.0),
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-30", 800, 10.0, 8000.0),
        InsiderTxn("X", "Bob", "CFO", "P", "2024-05-30", 1500, 10.0, 15000.0),
    ]
    sig = cluster_signal(txns)
    assert sig is not None
    assert sig["insider_count"] == 2  # Alice's two qualify when summed


def test_cluster_signal_window_exceeded():
    # Two insiders but transactions 10 days apart
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-01", 2000, 10.0, 20000.0),
        InsiderTxn("X", "Bob", "CFO", "P", "2024-05-15", 2000, 10.0, 20000.0),
    ]
    assert cluster_signal(txns) is None


def test_cluster_signal_only_sales():
    txns = [
        InsiderTxn("X", "Alice", "CEO", "S", "2024-05-29", 2000, 10.0, 20000.0),
        InsiderTxn("X", "Bob", "CFO", "S", "2024-05-30", 2000, 10.0, 20000.0),
    ]
    assert cluster_signal(txns) is None


def test_cluster_signal_mixed_buys_and_sales():
    # Only buys count
    txns = [
        InsiderTxn("X", "Alice", "CEO", "P", "2024-05-29", 1500, 10.0, 15000.0),
        InsiderTxn("X", "Alice", "CEO", "S", "2024-05-29", 100, 100.0, 10000.0),
        InsiderTxn("X", "Bob", "CFO", "P", "2024-05-30", 1500, 10.0, 15000.0),
    ]
    sig = cluster_signal(txns)
    assert sig is not None
    assert sig["insider_count"] == 2


def test_scan_universe_basic():
    universe = ["A", "B", "C"]

    def fetcher(sym):
        if sym == "A":
            return [
                InsiderTxn("A", "X", "", "P", "2024-05-29", 1500, 10.0, 15000.0),
                InsiderTxn("A", "Y", "", "P", "2024-05-30", 1500, 10.0, 15000.0),
            ]
        return []

    clusters = scan_universe(universe, fetcher, max_workers=2)
    assert len(clusters) == 1
    assert clusters[0]["symbol"] == "A"


def test_scan_universe_checkpoint():
    universe = ["A"] * 5
    checkpoints = []

    def fetcher(_):
        return []

    scan_universe(
        universe, fetcher, max_workers=2,
        checkpoint_every=2, on_checkpoint=lambda n, c: checkpoints.append(n),
    )
    # Checkpoint should fire at completion-counts 2 and 4
    assert 2 in checkpoints


def test_scan_universe_progress():
    universe = ["A"] * 3
    seen = []

    scan_universe(
        universe, lambda _: [], max_workers=2,
        on_progress=lambda done, total: seen.append((done, total)),
    )
    assert len(seen) == 3


def test_scan_universe_swallows_fetcher_errors():
    def boom(_):
        raise RuntimeError("nope")

    out = scan_universe(["A", "B"], boom, max_workers=2)
    assert out == []


# Need pytest at module scope for parse_form4 test approx
import pytest  # noqa: E402
