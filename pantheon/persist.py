"""CAS-based persistence to a git branch.

The persist() function is the single entry point. It uses git plumbing
(hash-object, read-tree, update-index, write-tree, commit-tree, push)
rather than porcelain so the working tree is never disturbed. The scratch
index is isolated by setting GIT_INDEX_FILE.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import uuid
from typing import Optional, Union


# Each god owns files whose paths match one of these prefixes. shared files
# (the dashboard) are owned by no specific god but may be written by any.
OWNERSHIP_PREFIXES: dict[str, list[str]] = {
    "oracle": [
        "cache/oracle_",
        "cache/dossier",
        "cache/screen_",
        "cache/smart_money",
        "cache/multi_lens",
        "cache/insider_clusters",
        "cache/oracle/",
    ],
    "delphi": [
        "cache/delphi_",
        "cache/delphi/",
    ],
    "achilles": [
        "cache/achilles_",
        "cache/achilles/",
    ],
    "midas": [
        "cache/midas_",
        "cache/midas/",
    ],
    "shared": [
        "cache/trinity_",
        "cache/shared_",
        "trinity_dashboard.html",
    ],
    "ghost_achilles": [
        "cache/ghost_achilles_",
    ],
    "ghost_delphi": [
        "cache/ghost_delphi_",
    ],
    "ghost_oracle": [
        "cache/ghost_oracle_",
    ],
    "ghost_midas": [
        "cache/ghost_midas_",
    ],
    "buzz": [
        "cache/buzz_",
    ],
    "ghost_buzz": [
        "cache/ghost_buzz_",
    ],
    "ghost_nemesis": [
        "cache/ghost_nemesis_",
        "cache/nemesis_pipeline.json",
        "cache/nemesis_dossiers.json",
        "cache/nemesis_cadence.json",
    ],
    "nemesis": [
        "cache/nemesis_sleeve.json",
        "cache/nemesis_ledger.jsonl",
        "cache/nemesis_curve.json",
    ],
    "ghost_proteus": [
        "cache/ghost_proteus_",
    ],
    "proteus": [
        "cache/proteus_",
    ],
}


# These files must never disappear from the branch after a persist that
# inherited from a parent containing them.
GUARD_FILES: list[str] = [
    "cache/oracle_sleeve.json",
    "cache/delphi_sleeve.json",
    "cache/achilles_sleeve.json",
    "cache/midas_sleeve.json",
    "cache/nemesis_sleeve.json",
    "cache/proteus_sleeve.json",
    # The prereg forbids journal resets after the first graded trade; this
    # makes the normal persist path enforce it mechanically (2026-07-04,
    # Proteus self-review finding #4). Out-of-band git surgery can still
    # bypass it — that is a deliberate operator act, not an accident.
    "cache/proteus_journal.jsonl",
    # The lab registry holds refuted-terminal verdicts; losing it would
    # silently permit the re-cuts the one-dataset rule forbids.
    "cache/proteus_lab.json",
    "cache/oracle_screen.json",
    "cache/oracle_prescreener.json",
    "cache/oracle_dossiers.json",
]


class IntegrityError(Exception):
    """Raised when a persist would cause a guard file to vanish."""


class PushRejected(Exception):
    """Raised when the remote rejected a push (e.g. non-fast-forward)."""


def owns(god: str, path: str) -> bool:
    god = god.lower()
    prefixes = OWNERSHIP_PREFIXES.get(god, [])
    return any(path.startswith(p) for p in prefixes)


def _run(args, cwd=None, env=None, *, check=True, input_bytes: Optional[bytes] = None):
    p = subprocess.run(
        args, cwd=cwd, env=env,
        input=input_bytes,
        capture_output=True,
    )
    if check and p.returncode != 0:
        raise RuntimeError(
            f"git failed ({p.returncode}): {' '.join(args)}: {p.stderr.decode(errors='replace')}"
        )
    return p


def _fetch_tip(remote: str, branch: str, repo_dir: str) -> Optional[str]:
    """Return the SHA of remote/branch, or None if it doesn't exist."""
    # Best-effort fetch; ignore failures (offline / not yet pushed).
    _run(["git", "fetch", remote, branch], cwd=repo_dir, check=False)
    p = _run(
        ["git", "rev-parse", "--verify", f"refs/remotes/{remote}/{branch}"],
        cwd=repo_dir, check=False,
    )
    if p.returncode == 0:
        return p.stdout.decode().strip()
    # Try local branch too — useful for tests and first-push scenarios.
    p = _run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
        cwd=repo_dir, check=False,
    )
    if p.returncode == 0:
        return p.stdout.decode().strip()
    return None


def _hash_object(content: bytes, repo_dir: str) -> str:
    p = _run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=repo_dir, input_bytes=content,
    )
    return p.stdout.decode().strip()


def _index_add(path: str, sha: str, scratch_index: str, repo_dir: str) -> None:
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = scratch_index
    _run(
        ["git", "update-index", "--add",
         "--cacheinfo", f"100644,{sha},{path}"],
        cwd=repo_dir, env=env,
    )


def _ls_tree_files(treeish: str, repo_dir: str) -> set[str]:
    p = _run(
        ["git", "ls-tree", "-r", "--name-only", treeish],
        cwd=repo_dir, check=False,
    )
    if p.returncode != 0:
        return set()
    out = p.stdout.decode().strip()
    if not out:
        return set()
    return set(out.split("\n"))


def _integrity_check(
    tree_sha: str, parent_tip: Optional[str], repo_dir: str
) -> Optional[str]:
    """Returns None if OK; otherwise the path of the missing guard file."""
    if not parent_tip:
        return None
    new_files = _ls_tree_files(tree_sha, repo_dir)
    parent_files = _ls_tree_files(parent_tip, repo_dir)
    for guard in GUARD_FILES:
        if guard in parent_files and guard not in new_files:
            return guard
    return None


def persist(
    god: str,
    files: dict[str, Union[str, bytes]],
    *,
    branch: str = "claude/live",
    remote: str = "origin",
    repo_dir: str = ".",
    max_retries: int = 6,
    base_backoff: float = 1.0,
    backoff_factor: float = 1.5,
    message: Optional[str] = None,
    push: bool = True,
    sleep: Optional[callable] = None,
) -> str:
    """Persist this god's owned files to the state branch.

    Returns the SHA of the new commit on success. Raises on irrecoverable
    failure.

    Files passed in that are NOT owned by `god` are silently ignored — the
    rule "each god only writes its own files" is enforced here.
    """
    god = god.lower()
    sleep = sleep or time.sleep
    if message is None:
        message = f"{god}: state update"

    norm: dict[str, bytes] = {}
    for p, c in files.items():
        norm[p] = c.encode("utf-8") if isinstance(c, str) else bytes(c)
    owned = {p: c for p, c in norm.items() if owns(god, p)}
    if not owned:
        raise ValueError(
            f"persist({god!r}) was called with no files this god owns; "
            f"check ownership prefixes"
        )

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        scratch = os.path.join(
            tempfile.gettempdir(), f"pantheon-idx-{uuid.uuid4().hex}"
        )
        try:
            tip = _fetch_tip(remote, branch, repo_dir)
            env = dict(os.environ)
            env["GIT_INDEX_FILE"] = scratch

            if tip:
                _run(["git", "read-tree", tip], cwd=repo_dir, env=env)
            else:
                # Empty index: read empty tree
                _run(["git", "read-tree", "--empty"], cwd=repo_dir, env=env)

            for path, content in owned.items():
                sha = _hash_object(content, repo_dir)
                _index_add(path, sha, scratch, repo_dir)

            tree_sha = _run(["git", "write-tree"], cwd=repo_dir, env=env).stdout.decode().strip()

            missing = _integrity_check(tree_sha, tip, repo_dir)
            if missing:
                raise IntegrityError(f"guard file would vanish: {missing}")

            args = ["git", "commit-tree", tree_sha, "-m", message]
            if tip:
                args.extend(["-p", tip])
            commit = _run(args, cwd=repo_dir).stdout.decode().strip()

            if push:
                # Non-force push: fail if non-fast-forward (someone else committed).
                p = _run(
                    ["git", "push", remote, f"{commit}:refs/heads/{branch}"],
                    cwd=repo_dir, check=False,
                )
                if p.returncode != 0:
                    last_error = PushRejected(p.stderr.decode(errors="replace"))
                    raise last_error
                # Refresh remote-tracking ref so the next fetch_tip sees current state.
                _run(
                    ["git", "update-ref", f"refs/remotes/{remote}/{branch}", commit],
                    cwd=repo_dir, check=False,
                )
            else:
                _run(["git", "update-ref", f"refs/heads/{branch}", commit], cwd=repo_dir)
            return commit
        except (PushRejected, IntegrityError, RuntimeError) as e:
            last_error = e
            sleep_t = base_backoff * (backoff_factor ** attempt)
            sleep(sleep_t)
        finally:
            if os.path.exists(scratch):
                try:
                    os.unlink(scratch)
                except OSError:
                    pass
    raise RuntimeError(
        f"persist failed after {max_retries} retries: {last_error}"
    )
