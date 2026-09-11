"""Guards on the ghost-Oracle RUNNER (run_ghost_oracle.py), not the library.

These cover the pre-persist aborts, which exist because the ghost book has twice
written a fabricated curve point that was indistinguishable from a real one:

  2026-08-03  a quote-cache envelope was read with the flat reader, the bare
              `except` swallowed it, every name marked at its ENTRY price, and a
              flawless 0.00% day landed in the curve.  Fixed by the envelope
              reader + MIN_MARK_COVERAGE.
  2026-08-11  the broker was unavailable, the run fell back to a DAY-OLD cache,
              passed MIN_MARK_COVERAGE at 203/203 = 100%, and wrote a point whose
              equity matched the prior day to six decimals with SPY_price 0.0.
              Coverage is not freshness; a stale cache fails silently, which is
              worse than a sparse one.

The runner is a flat script, so these drive it as a subprocess in a temp cwd and
assert on the exit code.  Each guard has its own exit code so a scheduler can
tell "no data" from "stale data" from "no benchmark".
"""
import json
import os
import subprocess
import sys
from datetime import date, timedelta

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(REPO, "run_ghost_oracle.py")

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

EXIT_STALE_CACHE = 3
EXIT_NO_BENCHMARK = 4


def _write(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def _make_workspace(tmp_path, quotes):
    """A minimal cache/ the runner can consume: one open paper position."""
    cache = tmp_path / "cache"
    _write(str(cache / "oracle_screen.json"), [])
    _write(str(cache / "oracle_dossiers.json"), [])
    _write(str(cache / "ghost_oracle_ledger.json"), [{
        "symbol": "AAA",
        "entry_date": "2026-01-02",
        "entry_price": 10.0,
        "horizon_days": 365,
        "source": "screen",
        "features": {},
        "exit_date": "",
        "exit_price": 0.0,
        "graded_return": None,
    }])
    _write(str(cache / "ghost_oracle_quotes.json"), quotes)
    return tmp_path


def _run(cwd):
    return subprocess.run(
        [sys.executable, RUNNER],
        cwd=str(cwd), capture_output=True, text=True, timeout=300,
    )


def _curve(cwd):
    p = cwd / "cache" / "ghost_oracle_curve.json"
    return json.load(open(p)) if p.exists() else []


def test_stale_unstamped_cache_aborts_before_persist(tmp_path):
    """A flat cache with FULL coverage but no as-of stamp must not mark.

    This is the 2026-08-11 shape exactly: 100% of the open book priceable, so
    MIN_MARK_COVERAGE passes cleanly, and every price is from a prior session.
    """
    ws = _make_workspace(tmp_path, {"AAA": 11.0, "SPY": 700.0})
    res = _run(ws)
    assert res.returncode == EXIT_STALE_CACHE, res.stderr
    assert "not stamped for today" in res.stderr
    assert _curve(ws) == [], "a stale run must leave no curve point behind"


def test_yesterdays_stamped_cache_aborts_before_persist(tmp_path):
    """An envelope stamped for a PRIOR day is stale even though it is stamped."""
    ws = _make_workspace(tmp_path, {"asof": YESTERDAY,
                                    "prices": {"AAA": 11.0, "SPY": 700.0}})
    res = _run(ws)
    assert res.returncode == EXIT_STALE_CACHE, res.stderr
    assert YESTERDAY in res.stderr
    assert _curve(ws) == []


def test_missing_benchmark_aborts_before_persist(tmp_path):
    """A today-stamped cache with no SPY still cannot produce a usable point.

    A curve point carrying SPY_price 0.0 is uninterpretable and silently breaks
    every excess-return reading taken after it.
    """
    ws = _make_workspace(tmp_path, {"asof": TODAY, "prices": {"AAA": 11.0}})
    res = _run(ws)
    assert res.returncode == EXIT_NO_BENCHMARK, res.stderr
    assert "benchmark leg is required" in res.stderr
    assert _curve(ws) == []


def test_fresh_stamped_cache_with_benchmark_marks_normally(tmp_path):
    """The happy path: today-stamped prices for the whole book plus SPY."""
    ws = _make_workspace(tmp_path, {"asof": TODAY,
                                    "prices": {"AAA": 11.0, "SPY": 700.0}})
    res = _run(ws)
    assert res.returncode == 0, res.stderr
    curve = _curve(ws)
    assert len(curve) == 1
    point = curve[-1]
    assert point["date"] == TODAY
    # Marked at the fresh quote (11.0), not the 10.0 entry price.
    assert point["benchmark"]["SPY_price"] == pytest.approx(700.0)
    assert point["equity"] > 0
