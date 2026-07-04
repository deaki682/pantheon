"""Reusable event-population catalogs for lab studies.

Every house study so far spent most of its wall-clock rebuilding its
population from scratch — the complete Form 4 sweep, the full spinoff
Form 10 catalog, the 8-K exhibit population. This module makes each of
those a build-once, cite-forever asset: an index at
`cache/shared_populations.json` and one rows file per population at
`cache/shared_pop_<slug>.json`, owned by the `shared` prefix.

Rules the writer enforces:
- `definition` states the complete-population criteria (what's in, over
  what window, from what source) — the selection-bias disclosure;
- `coverage_note` states what is KNOWN MISSING (delisted names the
  source can't serve, date gaps, rate-limit skips) — the survivorship
  disclosure. "complete" is an acceptable note only if you can say why;
- `source` is specific (EDGAR index path, URL, vendor+date);
- rows are non-empty dicts; a saved-empty population is refused loudly.

A population is DATA, not a decision: re-saving a slug replaces rows
(e.g. extending the window) — the one-dataset-one-decision rule lives
in shared.lab, which records which population version a backtest used
via the index's `built` date.
"""
from __future__ import annotations

import json
import os
from typing import Iterable

INDEX_PATH = "cache/shared_populations.json"


def _rows_path(slug: str, index_path: str = INDEX_PATH) -> str:
    base = os.path.dirname(index_path) or "."
    return os.path.join(base, f"shared_pop_{slug}.json")


def load_index(index_path: str = INDEX_PATH) -> dict:
    if not os.path.exists(index_path):
        return {"populations": {}}
    try:
        with open(index_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"populations": {}}
    data.setdefault("populations", {})
    return data


def save_population(
    slug: str,
    rows: Iterable[dict],
    *,
    definition: str,
    source: str,
    coverage_note: str,
    built: str,
    index_path: str = INDEX_PATH,
) -> dict:
    """Write a population's rows + register it in the index.

    Returns the index entry. Refuses stubs — an undisclosed hole in a
    population becomes an invisible bias in every study that cites it.
    """
    if not str(slug).isidentifier():
        raise ValueError(f"slug must be identifier-like, got {slug!r}")
    rows = list(rows)
    if not rows or not all(isinstance(r, dict) for r in rows):
        raise ValueError(f"{slug}: rows must be a non-empty list of dicts")
    if len(str(definition or "")) < 80:
        raise ValueError(
            f"{slug}: definition must state the complete-population "
            "criteria in >= 80 chars")
    if len(str(source or "").strip()) < 8:
        raise ValueError(f"{slug}: source must be specific (URL / index path)")
    if len(str(coverage_note or "")) < 60:
        raise ValueError(
            f"{slug}: coverage_note must state what is known missing "
            "(or why nothing is) in >= 60 chars")
    built = str(built)[:10]

    rpath = _rows_path(slug, index_path)
    os.makedirs(os.path.dirname(rpath) or ".", exist_ok=True)
    tmp = rpath + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"slug": slug, "rows": rows}, f, indent=1, sort_keys=True)
    os.replace(tmp, rpath)

    index = load_index(index_path)
    prev = index["populations"].get(slug)
    entry = {
        "definition": str(definition),
        "source": str(source).strip(),
        "coverage_note": str(coverage_note),
        "built": built,
        "n": len(rows),
        "file": rpath,
    }
    if prev:
        entry["previous_builds"] = prev.get("previous_builds", []) + [
            {"built": prev["built"], "n": prev["n"]}
        ]
    index["populations"][slug] = entry
    tmp = index_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(index, f, indent=1, sort_keys=True)
    os.replace(tmp, index_path)
    return entry


def load_population(slug: str, index_path: str = INDEX_PATH) -> list[dict]:
    index = load_index(index_path)
    entry = index["populations"].get(slug)
    if entry is None:
        raise KeyError(f"unknown population {slug!r}")
    with open(entry["file"]) as f:
        return json.load(f)["rows"]


def list_populations(index_path: str = INDEX_PATH) -> dict:
    """{slug: {built, n, definition, coverage_note, ...}} for browsing."""
    return load_index(index_path)["populations"]
