"""Spinoff dossier schema and honesty validation.

A SpinDossier is the contract the LLM analyst fills after reading a Form 10
(the SEC 10-12B registration statement every spinoff files before its shares
are distributed). The document is where the edge lives — index funds sell the
new stock for mechanical reasons in the first weeks after distribution, and
the only way to know whether what they're dumping is treasure or a garbage
barge is to actually read the filing. The LLM judges three things Greenblatt
identified as decisive: does management get equity in the SPINCO (incentive
alignment), what liabilities got dumped into it (garbage-barge risk), and who
must sell regardless of price (the forced-seller map). It never predicts
prices — expected_rerating_months is a patience budget, not a forecast.

validate() is an honesty gate, not a pessimism gate — the same spirit as the
falling-knife gate in oracle/research.py. It cannot tell a good read from a
bad one, but it can refuse a *lazy* one: a verdict with no articulated bear
case is not research, and an "own" on a spinoff where management holds no
equity or the balance sheet is a dumping ground is by definition not this
strategy's trade, whatever else it might be. Sloppy or over-bullish reads
fail loudly here instead of silently entering the ghost pipeline.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields

# Fields that must sit in [0, 1]. Kept in one place so validate() and the
# tests can't drift apart on which knobs are unit-interval scores.
_UNIT_FIELDS = ("incentive_alignment", "garbage_barge_risk", "neglect", "conviction")

# Prose fields that must be articulated, not stubbed. 20 chars is not a
# quality bar — it just makes "n/a" and "none" fail, forcing the analyst to
# write an actual sentence.
_PROSE_FIELDS = ("bull_case", "bear_case", "key_risk", "forced_seller_map")
_MIN_PROSE = 20

VERDICTS = {"own", "avoid", "watch"}

# The two Greenblatt tells an "own" must clear. Defaults are deliberately
# hostile (alignment 0.0, barge risk 1.0): an analyst who never touches them
# cannot produce an "own" by omission.
OWN_MIN_INCENTIVE = 0.5
OWN_MAX_GARBAGE = 0.6


@dataclass
class SpinDossier:
    """One spinoff, as judged from its Form 10.

    Defaults encode skepticism: incentive_alignment starts at 0.0 (assume
    management gets nothing until the filing shows otherwise) and
    garbage_barge_risk starts at 1.0 (assume the parent dumped its problems
    until the pro-formas prove clean). The analyst must earn every notch
    toward "own" by citing the document.
    """

    symbol: str
    parent: str
    cik: str = ""
    form10_url: str = ""
    distribution_date: str = ""
    incentive_alignment: float = 0.0  # 0-1: does mgmt get equity in the SPINCO?
    garbage_barge_risk: float = 1.0   # 0-1: liabilities/pension/debt dumped into it?
    neglect: float = 0.0              # 0-1: how orphaned (no coverage, index exile)
    forced_seller_map: str = ""       # WHO must sell and why (index funds, mandates)
    pro_forma_notes: str = ""         # what the pro-forma adjustments hide
    post_spin_insider_activity: str = ""  # Form 4 behavior since distribution —
                                      # the evidence trail behind any
                                      # incentive_alignment revision
                                      # (nemesis.insiders.render_summary)
    bull_case: str = ""
    bear_case: str = ""
    key_risk: str = ""
    verdict: str = "watch"            # "own" | "avoid" | "watch"
    conviction: float = 0.0           # 0-1
    expected_rerating_months: int = 6  # 1-12: patience budget, not a forecast
    researched_at: str = ""           # YYYY-MM-DD


def validate(d: SpinDossier) -> list[str]:
    """Return all problems with a dossier; empty list means valid.

    Every gate is reported (not just the first) so the analyst can fix a
    rejected dossier in one pass instead of playing whack-a-mole.

    The gates, and why each exists:
    - Unit fields in [0, 1]: scores outside the scale are meaningless and
      usually indicate the LLM confused a percentage with a fraction.
    - Non-empty symbol/parent/researched_at: an unattributed, undated dossier
      cannot be graded later.
    - Articulated prose (bull, bear, key risk, forced sellers): a verdict
      without a bear case is not research, and a spinoff dossier without a
      forced-seller map misses the entire reason the trade exists.
    - "own" requires incentive_alignment >= 0.5 AND garbage_barge_risk <= 0.6:
      the two Greenblatt tells. An "own" that fails them may still be a fine
      stock, but it is not THIS strategy's trade, and letting it through
      would contaminate the ghost's measurement of whether document judgment
      adds alpha. "watch" and "avoid" carry no such requirement — skepticism
      needs no permission slip.
    """
    problems: list[str] = []

    for name in _UNIT_FIELDS:
        val = getattr(d, name)
        if not isinstance(val, (int, float)) or isinstance(val, bool) or not 0.0 <= val <= 1.0:
            problems.append(f"{name} must be in [0, 1], got {val!r}")

    if d.verdict not in VERDICTS:
        problems.append(
            f"verdict must be one of {sorted(VERDICTS)}, got {d.verdict!r}"
        )

    months = d.expected_rerating_months
    if not isinstance(months, int) or isinstance(months, bool) or not 1 <= months <= 12:
        problems.append(
            f"expected_rerating_months must be an int in 1..12, got {months!r}"
        )

    for name in ("symbol", "parent", "researched_at"):
        if not str(getattr(d, name)).strip():
            problems.append(f"{name} must be non-empty")

    for name in _PROSE_FIELDS:
        val = str(getattr(d, name))
        if len(val) < _MIN_PROSE:
            problems.append(
                f"{name} must be at least {_MIN_PROSE} chars "
                f"(got {len(val)}) — an unarticulated read is not research"
            )

    if d.verdict == "own":
        if not (isinstance(d.incentive_alignment, (int, float))
                and d.incentive_alignment >= OWN_MIN_INCENTIVE):
            problems.append(
                f"verdict 'own' requires incentive_alignment >= {OWN_MIN_INCENTIVE} "
                f"(got {d.incentive_alignment!r}): management without equity in the "
                "spinco is the classic tell to pass"
            )
        if not (isinstance(d.garbage_barge_risk, (int, float))
                and d.garbage_barge_risk <= OWN_MAX_GARBAGE):
            problems.append(
                f"verdict 'own' requires garbage_barge_risk <= {OWN_MAX_GARBAGE} "
                f"(got {d.garbage_barge_risk!r}): a liability dumping ground is not "
                "this strategy's trade"
            )

    return problems


def make_dossier(**kwargs) -> SpinDossier:
    """Construct and validate a SpinDossier; raise ValueError if invalid.

    The single choke point for dossier creation — anything the pipeline
    builds goes through here so an invalid dossier can never exist as an
    object, only as an error message. All problems are joined into one
    message so one round-trip with the LLM fixes everything.
    """
    d = SpinDossier(**kwargs)
    problems = validate(d)
    if problems:
        raise ValueError("; ".join(problems))
    return d


def save_dossiers(path: str, dossiers: list[SpinDossier]) -> None:
    """Persist dossiers as {"dossiers": [...]} — atomic tmp + os.replace.

    Atomic so a crash mid-write can never leave a truncated JSON file for
    the next run to choke on (same pattern as midas/scanner.py).
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"dossiers": [asdict(d) for d in dossiers]}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_dossiers(path: str) -> list[SpinDossier]:
    """Load dossiers; missing file means an empty pool, not an error.

    Unknown keys are dropped for forward compatibility: a newer version of
    this schema can add fields and still have its files read by older code
    without crashing. Loaded dossiers are NOT re-validated — validation
    guards entry into the pipeline (make_dossier), not re-hydration of state
    we already accepted; tightening a gate later must not brick old files.
    """
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    known = {f.name for f in fields(SpinDossier)}
    out: list[SpinDossier] = []
    for raw in data.get("dossiers", []):
        out.append(SpinDossier(**{k: v for k, v in raw.items() if k in known}))
    return out
