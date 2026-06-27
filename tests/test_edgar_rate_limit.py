"""Rate limiter is global, thread-safe, and shared by all callers."""
import threading
import time

import pytest

from shared.edgar import _RATE, set_rate_limit


def test_rate_limiter_paces_calls(monkeypatch):
    """Two back-to-back acquires should be at least min_interval apart."""
    set_rate_limit(20.0)  # 20/s -> 50ms min interval
    t0 = time.monotonic()
    _RATE.acquire()
    _RATE.acquire()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.04  # allow a few ms of jitter below 50ms


def test_rate_limiter_thread_safe():
    """8 threads doing 3 acquires each should serialize to ~ 24 * min_interval total."""
    set_rate_limit(50.0)  # 50/s -> 20ms
    n_threads, n_calls = 8, 3
    barrier = threading.Barrier(n_threads)

    def worker():
        barrier.wait()
        for _ in range(n_calls):
            _RATE.acquire()

    t0 = time.monotonic()
    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.monotonic() - t0
    # 24 acquires / 50 per sec >= ~0.46s. Allow generous upper bound.
    assert elapsed >= 0.40
    set_rate_limit(8.0)  # restore default


def test_set_rate_limit_changes_pacing():
    set_rate_limit(1000.0)
    t0 = time.monotonic()
    for _ in range(10):
        _RATE.acquire()
    assert time.monotonic() - t0 < 0.5  # 10 calls at 1000/s should be < 0.5s
    set_rate_limit(8.0)
