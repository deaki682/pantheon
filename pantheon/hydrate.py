"""Hydrate the local cache/ directory from the claude/live state branch.

Every slash command should call hydrate() as its first step so that the
session starts with real data instead of empty defaults.  The function is
idempotent within a session — the second call is a no-op unless force=True.
"""
from __future__ import annotations

import logging
import os
import subprocess

log = logging.getLogger(__name__)

_hydrated = False


def hydrate(
    *,
    branch: str = "claude/live",
    remote: str = "origin",
    repo_dir: str = ".",
    paths: list[str] | None = None,
    force: bool = False,
) -> bool:
    """Restore cache files from the state branch into the working tree.

    Parameters
    ----------
    branch : str
        The state branch (default ``claude/live``).
    remote : str
        Git remote name.
    repo_dir : str
        Root of the git repo.
    paths : list[str] | None
        Specific paths to restore (e.g. ``["cache/oracle_screen.json"]``).
        If *None*, restores the entire ``cache/`` directory.
    force : bool
        Re-run even if hydrate() already succeeded this session.

    Returns
    -------
    bool
        True if files were restored, False if the branch doesn't exist or
        fetch failed (offline, first push, etc.).
    """
    global _hydrated
    if _hydrated and not force:
        return True

    ref = f"refs/remotes/{remote}/{branch}"

    # 1. Fetch the state branch (best-effort).
    subprocess.run(
        ["git", "fetch", remote, branch, "--depth=1"],
        cwd=repo_dir,
        capture_output=True,
        timeout=30,
    )

    # 2. Verify the ref exists.
    p = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        cwd=repo_dir,
        capture_output=True,
    )
    if p.returncode != 0:
        log.warning("hydrate: %s not found — starting with local cache only", ref)
        return False

    # 3. Ensure cache/ exists.
    os.makedirs(os.path.join(repo_dir, "cache"), exist_ok=True)

    # 4. Checkout files from the state branch into the working tree.
    checkout_paths = paths or ["cache/"]
    p = subprocess.run(
        ["git", "--work-tree=.", "checkout", f"{remote}/{branch}", "--"] + checkout_paths,
        cwd=repo_dir,
        capture_output=True,
    )
    if p.returncode != 0:
        stderr = p.stderr.decode(errors="replace").strip()
        if stderr:
            log.warning("hydrate: checkout failed: %s", stderr)
        return False

    # 5. Unstage the restored files so they don't pollute the code branch.
    subprocess.run(
        ["git", "reset", "HEAD", "--"] + checkout_paths,
        cwd=repo_dir,
        capture_output=True,
    )

    _hydrated = True
    restored = ", ".join(checkout_paths)
    log.info("hydrate: restored %s from %s/%s", restored, remote, branch)
    return True
