"""Resolved-event sweep — spec-driven EDGAR full-text search (Proteus v3).

Runs the 12-family post-resolution repricing hunt defined in
``cache/proteus_sweep_spec.json`` (the channel that produced the ABUS entry)
as one command instead of a hand-rewritten inline script each session.

The output is a deduped hit list with an ``exhibit_only`` pre-screen flag for
the batch-kill class (EX-1./EX-3./EX-4./EX-10. boilerplate with no 8-K body
match). The flag narrows the read; the kill itself stays a judgment call.

Network goes through ``shared.edgar.http_get`` (rate-limited, retrying);
tests inject ``fetch``.

CLI: ``python -m proteus.sweep 2026-08-14 2026-08-16``
"""
from __future__ import annotations

import json
from typing import Callable, Optional

from shared import edgar

SPEC_PATH = "cache/proteus_sweep_spec.json"

# Exhibit prefixes whose phrase matches are near-always indenture/credit/
# underwriting/charter boilerplate (the standing batch-kill class).
EXHIBIT_BOILERPLATE_PREFIXES = ("EX-1.", "EX-3.", "EX-4.", "EX-10.")

# Forms the sweep queries. 8-K alone was the original list and it is blind to
# the schedules a capital return actually COMMENCES on: ABUS announced its
# Dutch auction in an 8-K (caught 8/21) but commenced it on an SC TO-I
# (2026-08-24, missed — found only because ABUS was already a held position).
# The tender schedules carry the terms that decide entry and sizing (band,
# odd-lot preferential acceptance, expiry), so they belong in the sweep.
DEFAULT_FORMS = "8-K,SC TO-I,SC TO-C"


def load_spec(path: str = SPEC_PATH) -> dict:
    """Load the sweep spec; refuse to run without its families list."""
    with open(path) as f:
        spec = json.load(f)
    if not spec.get("families"):
        raise ValueError(f"sweep spec at {path} has no families")
    return spec


def family_tag(family: str) -> str:
    """Short tag for a family query: first word of its first quoted phrase."""
    return family.split()[0].strip('"')


def _default_fetch(params: dict) -> dict:
    return json.loads(edgar.http_get(edgar.SEARCH_URL, params=params))


def is_exhibit_only(file_types: set) -> bool:
    """True when every matched doc is batch-kill exhibit boilerplate."""
    known = {t for t in file_types if t}
    return bool(known) and all(
        t.startswith(EXHIBIT_BOILERPLATE_PREFIXES) for t in known
    )


def run_sweep(
    startdt: str,
    enddt: str,
    spec: Optional[dict] = None,
    fetch: Optional[Callable[[dict], dict]] = None,
) -> list:
    """Query every spec family over [startdt, enddt], dedupe by accession.

    Returns hits sorted by (date, adsh):
    ``{adsh, date, names, file_types, families, exhibit_only}``.
    """
    spec = spec or load_spec()
    fetch = fetch or _default_fetch
    forms = spec.get("forms") or DEFAULT_FORMS
    hits: dict = {}
    for family in spec["families"]:
        params = {"q": family, "forms": forms, "startdt": startdt, "enddt": enddt}
        data = fetch(params)
        for h in data.get("hits", {}).get("hits", []):
            src = h.get("_source", {})
            adsh = src.get("adsh")
            if not adsh:
                continue
            row = hits.setdefault(
                adsh,
                {
                    "adsh": adsh,
                    "date": src.get("file_date", ""),
                    "names": src.get("display_names", []),
                    "file_types": set(),
                    "families": set(),
                },
            )
            row["file_types"].add(src.get("file_type", ""))
            row["families"].add(family_tag(family))
    out = []
    for row in sorted(hits.values(), key=lambda r: (r["date"], r["adsh"])):
        row["exhibit_only"] = is_exhibit_only(row["file_types"])
        row["file_types"] = sorted(t for t in row["file_types"] if t)
        row["families"] = sorted(row["families"])
        out.append(row)
    return out


def report(hits: list) -> str:
    """One line per hit; exhibit-only batch-kill candidates flagged [EX]."""
    lines = [f"{len(hits)} unique accessions"]
    for h in hits:
        flag = "[EX] " if h["exhibit_only"] else "     "
        names = "; ".join(h["names"]) or "?"
        lines.append(
            f"{flag}{h['date']} {h['adsh']} {names} "
            f"fams={','.join(h['families'])} types={','.join(h['file_types'])}"
        )
    reads = sum(1 for h in hits if not h["exhibit_only"])
    lines.append(f"{reads} need a read ({len(hits) - reads} exhibit-only batch-kill candidates)")
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m proteus.sweep <startdt> <enddt>  (YYYY-MM-DD)")
        return 2
    print(report(run_sweep(args[0], args[1])))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
