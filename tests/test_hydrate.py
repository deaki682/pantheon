import sys
from unittest import mock

import pytest


# pantheon.__init__ exports `hydrate` as a function, which shadows the
# `pantheon.hydrate` module in attribute lookups.  Access the real module
# through sys.modules so mock.patch targets the right object.
_mod = sys.modules.setdefault(
    "pantheon.hydrate",
    __import__("pantheon.hydrate", fromlist=["hydrate"]),
)

from pantheon.hydrate import hydrate  # noqa: E402

# Use a dotted target that mock can resolve to the *module*, not the function.
_SUBPROC = f"{_mod.__name__}.subprocess.run"


@pytest.fixture(autouse=True)
def _reset():
    _mod._hydrated = False
    yield
    _mod._hydrated = False


def _ok(args, **kwargs):
    if "rev-parse" in args:
        return mock.Mock(returncode=0, stdout=b"abc123\n", stderr=b"")
    return mock.Mock(returncode=0, stdout=b"", stderr=b"")


def _no_branch(args, **kwargs):
    if "rev-parse" in args:
        return mock.Mock(returncode=128, stdout=b"", stderr=b"not found")
    return mock.Mock(returncode=0, stdout=b"", stderr=b"")


@mock.patch("os.makedirs")
def test_hydrate_idempotent(_makedirs):
    with mock.patch.object(_mod.subprocess, "run", side_effect=_ok):
        assert hydrate() is True
    with mock.patch.object(_mod.subprocess, "run") as m2:
        assert hydrate() is True
        m2.assert_not_called()


@mock.patch("os.makedirs")
def test_hydrate_force_reruns(_makedirs):
    with mock.patch.object(_mod.subprocess, "run", side_effect=_ok):
        hydrate()
    with mock.patch.object(_mod.subprocess, "run", side_effect=_ok) as m:
        hydrate(force=True)
        assert m.call_count > 0


def test_hydrate_returns_false_when_no_branch():
    with mock.patch.object(_mod.subprocess, "run", side_effect=_no_branch):
        assert hydrate() is False


@mock.patch("os.makedirs")
def test_hydrate_unstages_after_checkout(_makedirs):
    calls = []

    def track(args, **kwargs):
        calls.append(list(args))
        return _ok(args, **kwargs)

    with mock.patch.object(_mod.subprocess, "run", side_effect=track):
        hydrate()

    reset_calls = [c for c in calls if "reset" in c]
    assert len(reset_calls) == 1
    assert "HEAD" in reset_calls[0]
