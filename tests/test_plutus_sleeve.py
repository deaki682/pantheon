import pytest

from plutus.sleeve import (PlutusSleeve, HALT_DRAWDOWN, N_POSITIONS,
                           CASH_FLOOR, REBAL_BAND)


# ── constants ─────────────────────────────────────────────────────────

def test_constants():
    assert N_POSITIONS == 50
    assert HALT_DRAWDOWN == 0.40
    assert CASH_FLOOR == 0.02
    assert REBAL_BAND == 0.20


def test_init_is_unfunded_by_default():
    s = PlutusSleeve()
    assert s.name == "plutus"
    assert s.cash == 0.0
    assert s.contributed_cash == 0.0
    assert s.peak_equity == 0.0
    assert s.pending_funding is None
    # no cooldown — quarterly cadence
    assert s.cooldown_days == 0


# ── funding (the Delphi retirement sweep) ─────────────────────────────

def test_pending_before_sweep():
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi", "expected": "~$1,950"}
    assert s.is_funded() is False


def test_fund_clears_pending_and_seeds_cash():
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi"}
    s.fund(amount=1912.34, source="delphi", date="2026-07-07",
           note="Delphi retirement sweep")
    assert s.is_funded() is True
    assert s.cash == pytest.approx(1912.34)
    assert s.contributed_cash == pytest.approx(1912.34)
    assert s.pending_funding is None
    # peak advances to the funded cash so the breaker measures from real equity
    assert s.peak_equity == pytest.approx(1912.34)


def test_fund_is_additive_across_settlement_tranches():
    # Delphi's Monday sells settle T+1; the sweep can land in tranches.
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi"}
    s.fund(amount=1000.0, source="delphi", date="2026-07-07")
    assert s.pending_funding is None  # cleared on the first tranche
    s.fund(amount=912.0, source="delphi", date="2026-07-08")
    assert s.cash == pytest.approx(1912.0)
    assert s.contributed_cash == pytest.approx(1912.0)


def test_fund_rejects_nonpositive():
    s = PlutusSleeve()
    for bad in (0, -5, "x", None):
        with pytest.raises(ValueError):
            s.fund(amount=bad, source="delphi", date="2026-07-07")


def test_fund_only_clears_matching_source():
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi"}
    s.fund(amount=100.0, source="treasury", date="2026-07-07")
    # a non-matching source adds cash but does NOT clear the delphi marker
    assert s.pending_funding == {"from": "delphi"}
    assert s.is_funded() is False


# ── circuit breaker (identical semantics to Delphi/Midas) ─────────────

def test_check_halt_trips_at_40pct():
    s = PlutusSleeve()
    s.fund(amount=1000.0, source="delphi", date="2026-07-07")
    s.cash = 600.0  # 40% drawdown from the 1000 peak
    assert s.check_halt() is True
    assert s.halted is True


def test_check_halt_below_threshold():
    s = PlutusSleeve()
    s.fund(amount=1000.0, source="delphi", date="2026-07-07")
    s.cash = 700.0  # 30% drawdown
    assert s.check_halt() is False
    assert s.halted is False


def test_breaker_blocks_new_buys():
    s = PlutusSleeve()
    s.fund(amount=1000.0, source="delphi", date="2026-07-07")
    s.cash = 600.0
    s.check_halt()
    assert s.buy("AAPL", 1.0, 100.0, "2026-07-07") is False


# ── persistence round-trip carries peak + funding marker ──────────────

def test_roundtrip_preserves_funding_and_peak():
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi", "expected": "~$1,950"}
    s2 = PlutusSleeve.from_dict(s.to_dict())
    assert s2.pending_funding == {"from": "delphi", "expected": "~$1,950"}
    assert s2.is_funded() is False


def test_roundtrip_after_funding():
    s = PlutusSleeve()
    s.pending_funding = {"from": "delphi"}
    s.fund(amount=1912.34, source="delphi", date="2026-07-07")
    s.peak_equity = 2050.0
    s.halted = True
    s2 = PlutusSleeve.from_dict(s.to_dict())
    assert s2.is_funded() is True
    assert s2.peak_equity == pytest.approx(2050.0)
    assert s2.halted is True
    assert s2.cash == pytest.approx(1912.34)


def test_guard_registration():
    # Plutus must be wired into the shared guards so pre_trade_check /
    # filter_broker_to_gods / is_live all see him.
    from shared.guards import _LIVE_ENV, LEDGER_PATHS, SLEEVE_PATHS, is_live
    assert _LIVE_ENV["plutus"] == "PLUTUS_LIVE"
    assert LEDGER_PATHS["plutus"] == "cache/plutus_ledger.jsonl"
    assert SLEEVE_PATHS["plutus"] == "cache/plutus_sleeve.json"
    # default env has no PLUTUS_LIVE => paper
    assert is_live("plutus", env={}) is False
    assert is_live("plutus", env={"PLUTUS_LIVE": "true"}) is True


def test_persist_ownership():
    from pantheon.persist import owns, GUARD_FILES
    assert owns("plutus", "cache/plutus_sleeve.json") is True
    assert owns("plutus", "cache/plutus_ledger.jsonl") is True
    assert owns("plutus", "cache/delphi_sleeve.json") is False
    assert "cache/plutus_sleeve.json" in GUARD_FILES
