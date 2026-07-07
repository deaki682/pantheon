"""Network-free tests for Plutus's factor logic — the parts that decide WHICH
stocks the basket holds. The live deluxe book trades composite_basket(), so its
tie-breaking must be DETERMINISTIC (reproducible run-to-run and matching the
tracked control) — see the 2026-07-06 hash-seed bug."""
from plutus.strategy import _rank_map, composite_basket


def test_rank_map_ascending_breaks_ties_by_ticker():
    # low value = best (net issuance). C (0.5) best; A and B tie at 1.0 -> A before B.
    r = _rank_map({"B": 1.0, "A": 1.0, "C": 0.5}, ascending=True)
    assert r == {"C": 0, "A": 1, "B": 2}


def test_rank_map_descending_breaks_ties_by_ticker():
    # high value = best (gross profitability). A and B tie at 1.0 -> A before B; C last.
    r = _rank_map({"B": 1.0, "A": 1.0, "C": 0.5}, ascending=False)
    assert r == {"A": 0, "B": 1, "C": 2}


def test_rank_map_is_permutation_invariant():
    # same scores, different dict insertion order -> identical ranks (the bug was
    # that insertion order, driven by set iteration, leaked into the ranks).
    a = _rank_map({"X": 0.2, "Y": 0.2, "Z": 0.1}, ascending=True)
    b = _rank_map({"Y": 0.2, "Z": 0.1, "X": 0.2}, ascending=True)
    assert a == b == {"Z": 0, "X": 1, "Y": 2}


def test_composite_basket_deterministic_on_ties(monkeypatch):
    # Force a pile of ties so the tiebreak is exercised, with NO network: every
    # name has identical net-issuance and identical gross-profitability, so the
    # only thing that can order them is the deterministic ticker tiebreak.
    names = [f"T{i:02d}" for i in range(60)]
    monkeypatch.setattr(
        "plutus.strategy._two_factor_scores",
        lambda D, universe: ({t: 0.0 for t in names}, {t: 1.0 for t in names}),
    )
    b1 = composite_basket("2026-06-30", universe=set(names), size=50)
    b2 = composite_basket("2026-06-30", universe=set(reversed(names)), size=50)
    assert b1 == b2                       # reproducible regardless of set order
    assert b1 == sorted(names)[:50]       # pure ticker order under total ties
    assert len(b1) == 50 and len(set(b1)) == 50
