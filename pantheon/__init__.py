"""Pantheon — CAS-based state persistence to a git branch.

Three gods, one shared branch (`claude/live`). Each persist() call:
  1. Fetches the current branch tip
  2. Snapshots its tree into a scratch index (GIT_INDEX_FILE isolated)
  3. Overlays only this god's owned files
  4. Runs the integrity guard
  5. Commits with the fetched tip as parent
  6. Pushes without force; retries on rejection

Owners are prefix-keyed. Critical guard files cannot vanish.
"""
from .persist import (
    IntegrityError,
    PushRejected,
    persist,
    owns,
    GUARD_FILES,
    OWNERSHIP_PREFIXES,
)

__all__ = [
    "IntegrityError",
    "PushRejected",
    "persist",
    "owns",
    "GUARD_FILES",
    "OWNERSHIP_PREFIXES",
]
