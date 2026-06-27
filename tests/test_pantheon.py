"""Tests for pantheon CAS persistence. Uses a local bare repo as 'remote'."""
import os
import subprocess

import pytest

from pantheon import GUARD_FILES, IntegrityError, owns, persist


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repos(tmp_path):
    """Set up a local bare 'remote' and a working clone pointed at it."""
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    remote.mkdir()
    _git(["init", "--bare", "-b", "main", "."], cwd=remote)
    work.mkdir()
    _git(["init", "-b", "main", "."], cwd=work)
    _git(["remote", "add", "origin", str(remote)], cwd=work)
    _git(["config", "user.email", "t@t.com"], cwd=work)
    _git(["config", "user.name", "t"], cwd=work)
    return work, remote


def test_owns_oracle():
    assert owns("oracle", "cache/oracle_sleeve.json")
    assert owns("oracle", "cache/dossiers/foo.json")
    assert not owns("oracle", "cache/delphi_sleeve.json")


def test_owns_delphi():
    assert owns("delphi", "cache/delphi_sleeve.json")
    assert not owns("delphi", "cache/oracle_sleeve.json")


def test_owns_achilles():
    assert owns("achilles", "cache/achilles_sleeve.json")
    assert not owns("achilles", "cache/oracle_sleeve.json")


def test_owns_case_insensitive():
    assert owns("ORACLE", "cache/oracle_foo")


def test_persist_first_write_creates_branch(repos):
    work, remote = repos
    sha = persist(
        "oracle",
        {"cache/oracle_sleeve.json": '{"cash": 1000}'},
        repo_dir=str(work),
        max_retries=1,
        base_backoff=0,
    )
    assert sha
    # Branch exists on remote
    p = subprocess.run(
        ["git", "ls-remote", str(remote), "claude/live"],
        capture_output=True, text=True,
    )
    assert sha[:7] in p.stdout


def test_persist_second_write_advances(repos):
    work, _ = repos
    sha1 = persist(
        "oracle", {"cache/oracle_sleeve.json": "a"},
        repo_dir=str(work), max_retries=1, base_backoff=0,
    )
    sha2 = persist(
        "oracle", {"cache/oracle_sleeve.json": "b"},
        repo_dir=str(work), max_retries=1, base_backoff=0,
    )
    assert sha2 != sha1


def test_persist_ignores_files_not_owned(repos):
    work, _ = repos
    # Pass an Oracle file and a Delphi file — Delphi's is filtered out.
    sha = persist(
        "oracle",
        {
            "cache/oracle_sleeve.json": "a",
            "cache/delphi_sleeve.json": "should be ignored",
        },
        repo_dir=str(work), max_retries=1, base_backoff=0,
    )
    # The committed tree should NOT contain delphi_sleeve.json
    p = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", sha],
        cwd=str(work), capture_output=True, text=True,
    )
    files = p.stdout.strip().split("\n")
    assert "cache/oracle_sleeve.json" in files
    assert "cache/delphi_sleeve.json" not in files


def test_persist_no_owned_files_raises(repos):
    work, _ = repos
    with pytest.raises(ValueError):
        persist(
            "oracle", {"cache/delphi_sleeve.json": "x"},
            repo_dir=str(work), max_retries=1, base_backoff=0,
        )


def test_three_gods_persist_concurrently(repos):
    """Three persists in sequence — each god keeps the other gods' files."""
    work, _ = repos
    persist("oracle", {"cache/oracle_sleeve.json": "o"},
            repo_dir=str(work), max_retries=2, base_backoff=0)
    persist("delphi", {"cache/delphi_sleeve.json": "d"},
            repo_dir=str(work), max_retries=2, base_backoff=0)
    sha = persist("achilles", {"cache/achilles_sleeve.json": "a"},
                  repo_dir=str(work), max_retries=2, base_backoff=0)
    # Final tree contains all three.
    p = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", sha],
        cwd=str(work), capture_output=True, text=True,
    )
    files = set(p.stdout.strip().split("\n"))
    assert "cache/oracle_sleeve.json" in files
    assert "cache/delphi_sleeve.json" in files
    assert "cache/achilles_sleeve.json" in files


def test_integrity_guard_blocks_vanishing_file(repos, monkeypatch):
    """If we try to persist a tree that drops a guard file, it should fail.

    Simulate by writing the guard file via raw plumbing, then having Oracle
    persist nothing (an empty owned set raises) — instead, monkeypatch
    GUARD_FILES to include a path that we deliberately don't preserve.
    """
    work, _ = repos
    # Seed Oracle sleeve.
    persist("oracle", {"cache/oracle_sleeve.json": "v1"},
            repo_dir=str(work), max_retries=1, base_backoff=0)
    # Seed Delphi sleeve.
    persist("delphi", {"cache/delphi_sleeve.json": "v1"},
            repo_dir=str(work), max_retries=1, base_backoff=0)

    # Now monkey the OWNERSHIP_PREFIXES so Oracle "owns" delphi sleeve too,
    # and the integrity check should still catch attempts to remove it via
    # — actually a simpler test: integrity_check is invoked internally; verify
    # the check function directly.
    from pantheon.persist import _integrity_check
    # tree at HEAD on claude/live
    p = subprocess.run(
        ["git", "rev-parse", "refs/remotes/origin/claude/live"],
        cwd=str(work), capture_output=True, text=True,
    )
    tip = p.stdout.strip()
    # An empty tree as the new tree -> guard file vanishes
    empty_tree = subprocess.run(
        ["git", "hash-object", "-t", "tree", "--stdin"],
        cwd=str(work), input=b"", capture_output=True,
    )
    # Use mktree to make a true empty tree
    p2 = subprocess.run(
        ["git", "mktree"], cwd=str(work),
        input=b"", capture_output=True,
    )
    empty_sha = p2.stdout.decode().strip()
    missing = _integrity_check(empty_sha, tip, str(work))
    assert missing in GUARD_FILES


def test_persist_retries_on_failure(repos):
    """The retry loop must invoke its sleep() the right number of times."""
    work, _ = repos
    # Persist with an invalid remote so push fails and we exercise retries.
    calls = []
    with pytest.raises(RuntimeError):
        persist(
            "oracle",
            {"cache/oracle_sleeve.json": "a"},
            remote="does-not-exist-remote",
            repo_dir=str(work),
            max_retries=3,
            base_backoff=1.0,
            backoff_factor=1.5,
            sleep=lambda t: calls.append(t),
        )
    # 3 retries -> 3 sleep calls with backoff 1.0, 1.5, 2.25
    assert len(calls) == 3
    assert calls[0] == pytest.approx(1.0)
    assert calls[1] == pytest.approx(1.5)
    assert calls[2] == pytest.approx(2.25)
