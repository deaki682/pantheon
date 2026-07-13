"""Proteus v2 — the ENTRY SCHEMA (charter v2.1, art. 15).

Every per-entry duty the charter imposes, consolidated into one
machine-validated gate the journal writer enforces BEFORE accepting the
entry. Weakening any validation here is an integrity-gate offense
(art. 15); the floor tests (tests/test_proteus_floor.py, operator-owned)
pin the base journal behaviors underneath this layer, and this module
always calls proteus.journal.validate_decision first for the actions it
knows — the schema only ever ADDS refusals on top of the floor.

Record shapes (all JSONL journal lines, append-only):

- ``action: enter`` — a position-changing order. Base fields per
  proteus.journal, plus a ``charter`` dict carrying the Title I–IV
  duties (see ``validate_record``). Three variants:
  * a normal position (thesis + primary prediction + full sizing law),
  * ``charter.park: true`` (art. 27/1 — no thesis BY DESIGN, caps and
    ladders exempt, worst case still honest),
  * ``charter.staged.is_staged: true`` (art. 16 — minimum executable
    size, mechanics prediction in place of a thesis primary, excluded
    from ladders and trade calibration).
- ``action: exit`` — base fields per proteus.journal plus ``tax``
  (art. 20b: term + estimated consequence at the standing assumed rate).
- ``action: grade`` — the two-axis cell grade (art. 7) with the
  calibration fields (art. 10). New action, defined here.
- ``action: disposition`` — the shadow book (art. 8). New action.
- ``action: note`` — unchanged from the base journal.

Sizing context is passed in via ``EntryContext`` — equity, peak, open
worst cases, grade counts — so the arithmetic is checked against the
book as it IS, not as the entry claims it to be.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date

from proteus import calibration as cal
from proteus.journal import JournalError, validate_decision
from proteus.registry import require_class, require_tags

# Art. 1 — the Geometric Sizing Law.
SINGLE_CAP = 0.25          # single-position worst case <= 25% of equity
AGGREGATE_CAP = 0.60       # summed worst cases <= 60% of equity
PROBE_CAP = 0.10           # art. 2: absolute, never scales with art. 5
# Art. 1 worst-case honesty floors.
EQUITY_WC_FLOOR = 0.50     # single-name equity: >= 50% of notional
INDEX_WC_FLOOR = 0.20      # index fund: >= 20% x leverage of notional
# Art. 16 — staged deployment.
STAGED_MAX_NOTIONAL_PCT = 0.05
# Art. 1 — the park whitelists (1x S&P 500 / total-market; T-bill class).
PARK_INDEX_FUNDS = ("SPY", "VOO", "IVV", "SPLG", "VTI", "ITOT", "SCHB")
PARK_TBILL_FUNDS = ("SGOV", "BIL", "SHV")

INSTRUMENT_KINDS = ("single_name_equity", "index_fund", "merger_target",
                    "long_option")
DISPOSITION_VERDICTS = ("entered", "declined", "killed_at_screen", "avoid")

_PROSE = {
    "kill_switch_amenability": 40,   # invariant 2 clarification
    "cluster_check": 40,             # art. 3
    "tape_verification": 40,         # art. 19
    "wash_sale_check": 20,           # art. 20b
    "symbol_collision_check": 20,    # art. 20c
}
_WC_BASIS_FLOOR = 60                 # unattended framing, art. 1/4
_GRADING_RULE_FLOOR = 80             # art. 6
_LEDGER_CHECK_FLOOR = 60             # art. 13a
_LIFECYCLE_FLOOR = 60                # art. 20a
_TOL = 0.01                          # dollar tolerance on echoed arithmetic


class SchemaError(JournalError):
    """An entry that can't satisfy the charter is refused, listing every
    unmet duty at once — one round trip, not a scavenger hunt."""


@dataclass
class EntryContext:
    """The book as it is, for the sizing arithmetic (Title I)."""
    sleeve_equity: float
    peak_equity: float
    open_worst_cases_total: float = 0.0      # $ across all open positions
    class_open_worst_cases: float = 0.0      # $ across open positions in class
    class_real_grades: int = 0               # art. 2 ladder, this class
    total_real_grades: int = 0               # art. 2 Kelly step
    first_in_family: bool = False            # art. 13a
    kelly_multiplier: float = cal.KELLY_BASE  # from cal.allowed_kelly_multiplier
    registry: dict = field(default_factory=dict)


def _prose(errors: list, holder: dict, name: str, floor: int, duty: str) -> None:
    if len(str(holder.get(name) or "")) < floor:
        errors.append(f"{name} must be >= {floor} chars ({duty})")


def _require_worst_case(errors: list, record: dict, ch: dict) -> float:
    """Art. 1 honesty floors. Returns the journaled worst case in dollars
    (0.0 if malformed — the error list carries the refusal)."""
    wc = ch.get("worst_case") or {}
    amount = wc.get("amount")
    if not (isinstance(amount, (int, float)) and not isinstance(amount, bool)
            and amount > 0):
        errors.append("charter.worst_case.amount must be a positive dollar "
                      "number (invariant 1)")
        return 0.0
    _prose(errors, wc, "basis", _WC_BASIS_FLOOR,
           "art. 4: the UNATTENDED framing — computed to the next session "
           "guaranteed to fire, never to a stop nobody executes")
    notional = float(record.get("dollars") or 0)
    kind = ch.get("instrument_kind")
    if kind not in INSTRUMENT_KINDS:
        errors.append(f"charter.instrument_kind must be one of "
                      f"{INSTRUMENT_KINDS} (art. 1 floors key off it)")
        return float(amount)
    if kind == "single_name_equity":
        floor_amt = EQUITY_WC_FLOOR * notional
        if amount < floor_amt - _TOL and len(str(ch.get("senior_bound") or "")) < _WC_BASIS_FLOOR:
            errors.append(
                f"single-name equity worst case ${amount:,.2f} is below the "
                f"{EQUITY_WC_FLOOR:.0%}-of-notional floor ${floor_amt:,.2f} "
                "and no charter.senior_bound (>= 60 chars, contractual or "
                "senior enforceable) is stated (art. 1)")
    elif kind == "index_fund":
        lev = ch.get("leverage")
        if not (isinstance(lev, (int, float)) and lev >= 1):
            errors.append("index_fund entries must state charter.leverage "
                          ">= 1 (absolute value; inverse included) (art. 1)")
        else:
            floor_amt = INDEX_WC_FLOOR * lev * notional
            if amount < floor_amt - _TOL:
                errors.append(
                    f"index-fund worst case ${amount:,.2f} is below the "
                    f"20% x leverage floor ${floor_amt:,.2f} (art. 1)")
    elif kind == "merger_target":
        dbp = ch.get("deal_break_price")
        px = record.get("price")
        if not (isinstance(dbp, (int, float)) and dbp > 0):
            errors.append("merger_target entries must state "
                          "charter.deal_break_price > 0 (art. 1)")
        elif isinstance(px, (int, float)) and px > 0:
            floor_amt = notional * max(0.0, 1.0 - dbp / px)
            if amount < floor_amt - _TOL:
                errors.append(
                    f"merger-target worst case ${amount:,.2f} is below the "
                    f"deal-break computation ${floor_amt:,.2f} — the worst "
                    "case is the deal-break price, never the offer (art. 1)")
    elif kind == "long_option":
        if abs(amount - notional) > _TOL:
            errors.append(
                f"long-option worst case ${amount:,.2f} must equal the net "
                f"debit ${notional:,.2f} — the premium IS the bound "
                "(invariant 1)")
    return float(amount)


def _check_caps(errors: list, wc: float, ctx: EntryContext,
                staged: bool) -> None:
    """Arts. 1, 2, 5 — all limits compose by minimum."""
    eq = ctx.sleeve_equity
    if eq <= 0:
        errors.append("sleeve equity must be positive to size anything")
        return
    tier = cal.drawdown_tier(eq, ctx.peak_equity)
    scale = 0.5 if tier >= 1 else 1.0
    single = SINGLE_CAP * scale
    agg = AGGREGATE_CAP * scale
    if wc > single * eq + _TOL:
        errors.append(f"worst case ${wc:,.2f} exceeds the single-position "
                      f"cap {single:.1%} of equity ${single * eq:,.2f} "
                      f"(art. 1{'/5 halved' if scale < 1 else ''})")
    if ctx.open_worst_cases_total + wc > agg * eq + _TOL:
        errors.append(
            f"aggregate worst cases ${ctx.open_worst_cases_total + wc:,.2f} "
            f"would exceed {agg:.1%} of equity ${agg * eq:,.2f} (art. 1)")
    if staged:
        return  # staged entries are ladder-exempt (art. 16) but cap-bound
    if ctx.class_real_grades < cal.PROBE_CLASS_GRADES and wc > PROBE_CAP * eq + _TOL:
        errors.append(
            f"class has {ctx.class_real_grades} real-money grades (< "
            f"{cal.PROBE_CLASS_GRADES}) — probe size binds: worst case <= "
            f"{PROBE_CAP:.0%} of equity ${PROBE_CAP * eq:,.2f} (art. 2)")
    if (ctx.class_real_grades < cal.HALF_AGG_CLASS_GRADES
            and ctx.class_open_worst_cases + wc > 0.5 * agg * eq + _TOL):
        errors.append(
            f"class has {ctx.class_real_grades} real-money grades (< "
            f"{cal.HALF_AGG_CLASS_GRADES}) — class summed worst case <= half "
            f"the prevailing aggregate cap ${0.5 * agg * eq:,.2f} (art. 2)")


def _check_kelly(errors: list, ch: dict, wc: float, ctx: EntryContext) -> None:
    """Art. 2 — the Kelly cap binds on worst case as a fraction of equity,
    with payoff odds per unit of worst case. The p, payoff, fraction, and
    multiplier are shown in the entry itself and re-derived here."""
    k = ch.get("kelly") or {}
    p, b = k.get("p"), k.get("payoff_per_unit_worst_case")
    try:
        f_star = cal.kelly_fraction(float(p), float(b))
    except (TypeError, ValueError) as exc:
        errors.append(f"charter.kelly must carry p and "
                      f"payoff_per_unit_worst_case ({exc})")
        return
    if f_star <= 0:
        errors.append(
            f"the entry's own arithmetic says no edge: Kelly fraction "
            f"{f_star:.3f} <= 0 at p={p}, b={b} — refused (art. 2)")
        return
    if abs(float(k.get("fraction") or 0) - f_star) > 0.005:
        errors.append(f"charter.kelly.fraction {k.get('fraction')!r} does not "
                      f"match p - (1-p)/b = {f_star:.4f} (art. 2: the "
                      "arithmetic is shown in the entry)")
    mult = min(float(ctx.kelly_multiplier), cal.KELLY_MAX)
    if ctx.total_real_grades < cal.KELLY_STEP_GRADES:
        mult = min(mult, cal.KELLY_BASE)
    if abs(float(k.get("multiplier") or 0) - mult) > 1e-9:
        errors.append(f"charter.kelly.multiplier {k.get('multiplier')!r} != "
                      f"prevailing {mult} (art. 2)")
    cap = mult * f_star * ctx.sleeve_equity
    if wc > cap + _TOL:
        errors.append(
            f"worst case ${wc:,.2f} exceeds {mult:.2f} x Kelly ({f_star:.3f})"
            f" x equity = ${cap:,.2f} (art. 2)")
    stated = (ch.get("primary") or {}).get("stated_p")
    if stated is not None and abs(float(stated) - float(p)) > 1e-9:
        errors.append("primary.stated_p must equal kelly.p — the SAME "
                      "probability prices the bet and gets scored (art. 6)")


def _check_primary(errors: list, record: dict, ch: dict) -> None:
    """Art. 6 — exactly one primary, in P&L terms, gradable by a stranger."""
    pr = ch.get("primary") or {}
    if pr.get("direction") not in ("up", "down"):
        errors.append("primary.direction must be 'up' or 'down' (art. 6)")
    mag = pr.get("magnitude_pct")
    if not (isinstance(mag, (int, float)) and not isinstance(mag, bool)
            and mag > 0):
        errors.append("primary.magnitude_pct must be a positive number "
                      "(art. 6: direction, magnitude, date)")
    by = pr.get("by_date")
    try:
        if str(by) <= str(record.get("date")):
            errors.append(f"primary.by_date {by!r} must be after the entry "
                          "date (art. 6)")
        _date.fromisoformat(str(by))
    except (TypeError, ValueError):
        errors.append(f"primary.by_date must be an ISO date, got {by!r}")
    _prose(errors, pr, "grading_rule", _GRADING_RULE_FLOOR,
           "art. 6: the broker-tape numbers that decide HIT or MISS, "
           "computable by a reader who is not him")
    sp = pr.get("stated_p")
    if not (isinstance(sp, (int, float)) and 0.0 < float(sp) < 1.0):
        errors.append("primary.stated_p must be in (0,1) (art. 10)")
    hurdle = pr.get("cost_hurdle_pct")
    if not (isinstance(hurdle, (int, float)) and hurdle >= 0):
        errors.append("primary.cost_hurdle_pct must state the journaled "
                      "cost-and-slippage hurdle (art. 6: a threshold below "
                      "it grades MISS even if technically hit)")
    elif isinstance(mag, (int, float)) and mag <= hurdle:
        errors.append(f"primary.magnitude_pct {mag} sits at or below the "
                      f"cost hurdle {hurdle} — grades MISS by construction "
                      "(art. 6)")


def _check_spendable(errors: list, record: dict, ch: dict) -> None:
    """Art. 26a — the spendable arithmetic, journaled and re-derived."""
    sp = ch.get("spendable") or {}
    needed = ("sleeve_cash", "account_settled_bp", "other_gods_pending",
              "spendable")
    missing = [k for k in needed if not isinstance(sp.get(k), (int, float))]
    if missing:
        errors.append(f"charter.spendable missing numeric {missing} "
                      "(art. 26a — 'no deployment signal found' is recorded "
                      "as other_gods_pending: 0.0 with the note)")
        return
    derived = min(sp["sleeve_cash"],
                  sp["account_settled_bp"] - sp["other_gods_pending"])
    if abs(sp["spendable"] - derived) > _TOL:
        errors.append(f"charter.spendable.spendable {sp['spendable']} != "
                      f"min(sleeve cash, settled BP - other gods') = "
                      f"{derived:.2f} (art. 26a)")
    if float(record.get("dollars") or 0) > sp["spendable"] + _TOL:
        errors.append(f"dollars {record.get('dollars')} exceeds spendable "
                      f"{sp['spendable']} (art. 26a)")


def _validate_enter(record: dict, ctx: EntryContext | None) -> None:
    errors: list[str] = []
    ch = record.get("charter")
    if not isinstance(ch, dict):
        raise SchemaError(
            "enter is missing the charter dict — every position-changing "
            "entry carries its Title I-IV duties (art. 15)")
    if ctx is None:
        raise SchemaError("enter requires an EntryContext — the sizing law "
                          "binds against the book as it is (art. 15)")
    park = bool(ch.get("park"))
    staged = bool((ch.get("staged") or {}).get("is_staged"))
    if park and staged:
        errors.append("an entry cannot be both a park and a staged order")

    wc = _require_worst_case(errors, record, ch)

    if park:
        sym = str(record.get("symbol") or "").upper()
        if sym not in PARK_INDEX_FUNDS + PARK_TBILL_FUNDS:
            errors.append(
                f"{sym!r} is not a park instrument — parks are strictly "
                f"1x S&P 500/total-market {PARK_INDEX_FUNDS} or T-bill class "
                f"{PARK_TBILL_FUNDS} (art. 1)")
        if ch.get("primary"):
            errors.append("a park carries no thesis prediction BY DESIGN "
                          "(art. 27) — grade the posture under art. 13b, "
                          "not a primary")
        _prose(errors, ch, "park_reason", 40,
               "art. 1: why the sleeve is parked rather than hunting")
    else:
        _check_caps(errors, wc, ctx, staged)
        if staged:
            st = ch.get("staged") or {}
            _prose(errors, st, "mechanics_prediction", 60,
                   "art. 16: a mechanics prediction in place of a thesis "
                   "primary")
            _prose(errors, st, "code_change", 20,
                   "art. 16: the entry names the code change it exercises")
            if (float(record.get("dollars") or 0)
                    > STAGED_MAX_NOTIONAL_PCT * ctx.sleeve_equity + _TOL
                    and len(str(st.get("min_increment_note") or "")) < 40):
                errors.append(
                    "staged orders run at minimum executable size — normally "
                    f"<= {STAGED_MAX_NOTIONAL_PCT:.0%} of equity notional; a "
                    "one-increment minimum above that needs its journaled "
                    "note (art. 16)")
        else:
            _check_kelly(errors, ch, wc, ctx)
            _check_primary(errors, record, ch)
            if ctx.first_in_family:
                _prose(errors, ch, "ledger_check", _LEDGER_CHECK_FLOOR,
                       "art. 13a: rows searched + 'no refutation applies' or "
                       "the refutation quoted beside the new evidence")
        # class + tags bind for all non-park entries, staged included
        cls = ch.get("strategy_class")
        try:
            require_class(ctx.registry, cls)
        except Exception as exc:
            errors.append(str(exc))
        fm = ch.get("failure_modes")
        if not (isinstance(fm, list) and fm):
            errors.append("charter.failure_modes must be a non-empty list of "
                          "registered tags (art. 3)")
        else:
            try:
                require_tags(ctx.registry, "failure_mode", fm)
            except Exception as exc:
                errors.append(str(exc))
        jt = (ch.get("primary") or {}).get("judgment_type")
        if not staged:
            try:
                require_tags(ctx.registry, "judgment_type",
                             [jt] if jt else [])
                if not jt:
                    errors.append("primary.judgment_type is required at "
                                  "write time (art. 10)")
            except Exception as exc:
                errors.append(str(exc))
        cites = ch.get("citations")
        if not (isinstance(cites, list) and cites):
            errors.append("charter.citations must list the public sources "
                          "the thesis rests on (art. 18)")
        wake = ch.get("verified_wake") or {}
        if wake.get("status") not in ("verified", "none"):
            errors.append("charter.verified_wake.status must be 'verified' "
                          "or 'none' (art. 4)")
        _prose(errors, wake, "note", 40,
               "art. 4: what fires between sessions and who is awake — or "
               "why the unattended worst case already prices it")

    # duties common to every enter, parks included
    for name, floor in _PROSE.items():
        duty = {"kill_switch_amenability": "invariant 2 clarification: how "
                                           "this position liquidates if the "
                                           "kill fires",
                "cluster_check": "art. 3",
                "tape_verification": "art. 19: the broker quote checked, "
                                     "with its timestamp",
                "wash_sale_check": "art. 20b",
                "symbol_collision_check": "art. 20c"}[name]
        if park and name == "cluster_check":
            continue  # parks carry no failure-mode cluster by design
        _prose(errors, ch, name, floor, duty)
    _check_spendable(errors, record, ch)
    hand = ch.get("handoff")
    if hand is not None:
        for f2 in ("what", "deadline", "instruction"):
            if not hand.get(f2):
                errors.append(f"charter.handoff.{f2} is required (art. 25)")
        _prose(errors, hand, "solo_fallback", 40,
               "art. 25: what happens if the operator action never happens, "
               "with the worst case priced on that path")
    if record.get("instrument") == "option":
        _prose(errors, ch, "lifecycle", _LIFECYCLE_FLOOR,
               "art. 20a: assignment / auto-exercise / pin risk map across "
               "every unattended date")
    if errors:
        raise SchemaError("entry refused — unmet charter duties:\n- "
                          + "\n- ".join(errors))


def _validate_grade(record: dict) -> None:
    errors: list[str] = []
    for f in ("date", "symbol", "entry_date"):
        if not record.get(f):
            errors.append(f"grade.{f} is required (art. 28a: re-derivable)")
    tv = record.get("thesis_verdict")
    if tv not in cal.THESIS_VERDICTS:
        errors.append(f"thesis_verdict must be one of {cal.THESIS_VERDICTS}")
    pv = record.get("pnl_verdict")
    if pv not in cal.PNL_VERDICTS:
        errors.append(f"pnl_verdict must be one of {cal.PNL_VERDICTS}")
    cell = record.get("cell")
    if tv in cal.THESIS_VERDICTS and pv in cal.PNL_VERDICTS:
        thesis_hit = tv in ("HIT", "PARTIAL")  # PARTIAL routes HIT (art. 6)
        expected = {(True, "PAID"): "SKILL", (False, "PAID"): "LUCK",
                    (True, "UNPAID"): "UNLUCKY",
                    (False, "UNPAID"): "ERROR"}[(thesis_hit, pv)]
        if cell != expected:
            errors.append(f"cell {cell!r} contradicts the axes "
                          f"({tv}, {pv}) => {expected} (art. 7 — the cell is "
                          "derived, never chosen)")
    if tv == "PARTIAL":
        frac = record.get("realized_fraction")
        if not (isinstance(frac, (int, float)) and 0.0 <= float(frac) <= 1.0):
            errors.append("a PARTIAL grade carries realized_fraction in "
                          "[0,1] (art. 6)")
    sp = record.get("stated_p")
    if not (isinstance(sp, (int, float)) and 0.0 < float(sp) < 1.0):
        errors.append("grade.stated_p must echo the entry's stated p "
                      "(art. 10 — a stated probability that never gets "
                      "scored is a violation)")
    if not record.get("strategy_class"):
        errors.append("grade.strategy_class is required (art. 9)")
    if not record.get("judgment_type"):
        errors.append("grade.judgment_type is required (art. 10)")
    if "real_money" not in record or "shadow" not in record:
        errors.append("grade must state real_money and shadow booleans "
                      "(arts. 2, 8 — ladders unlock on real money only)")
    wcp = record.get("worst_case_pct_at_entry")
    if not (isinstance(wcp, (int, float)) and wcp >= 0):
        errors.append("grade.worst_case_pct_at_entry is required (art. 2's "
                      "1%-of-equity counting floor reads it)")
    if len(str(record.get("basis") or "")) < 60:
        errors.append("grade.basis must be >= 60 chars: the maturity tape "
                      "numbers against the grading rule, re-derivable by a "
                      "stranger (art. 28a)")
    if errors:
        raise SchemaError("grade refused:\n- " + "\n- ".join(errors))


def _validate_disposition(record: dict) -> None:
    errors: list[str] = []
    for f in ("date", "name"):
        if not record.get(f):
            errors.append(f"disposition.{f} is required (art. 8)")
    if record.get("verdict") not in DISPOSITION_VERDICTS:
        errors.append(f"disposition.verdict must be one of "
                      f"{DISPOSITION_VERDICTS} (art. 8)")
    if len(str(record.get("reason") or "")) < 20:
        errors.append("disposition.reason must be >= 20 chars — the one-line "
                      "mechanical reason at minimum (art. 8)")
    shadow = record.get("shadow_primary")
    if shadow is not None:
        for f in ("direction", "magnitude_pct", "by_date",
                  "hypothetical_dollars"):
            if shadow.get(f) in (None, ""):
                errors.append(f"shadow_primary.{f} is required — a gradable "
                              "shadow is a full counterfactual (art. 8)")
        if len(str(record.get("divergence") or "")) < 40:
            errors.append(
                "a gradable shadow exists only when a journaled pre-read "
                "divergence view existed — state it (>= 40 chars) or record "
                "a plain non-gradable AVOID (art. 8)")
    if errors:
        raise SchemaError("disposition refused:\n- " + "\n- ".join(errors))


def _validate_exit(record: dict) -> None:
    tax = record.get("tax") or {}
    errors: list[str] = []
    if tax.get("term") not in ("short", "long"):
        errors.append("exit.tax.term must be 'short' or 'long' (art. 20b)")
    for f in ("estimated_tax", "assumed_rate"):
        if not isinstance(tax.get(f), (int, float)):
            errors.append(f"exit.tax.{f} must be numeric (art. 20b — the "
                          "standing journaled assumed rate)")
    if errors:
        raise SchemaError("exit refused:\n- " + "\n- ".join(errors))


def validate_record(record: dict, ctx: EntryContext | None = None) -> dict:
    """The one gate (art. 15). Delegates the base-journal floor first for
    the actions it defines (the floor tests pin those behaviors), then
    layers the charter duties. Returns the record untouched on success."""
    if not isinstance(record, dict):
        raise SchemaError(f"record must be a dict, got {type(record).__name__}")
    action = record.get("action")
    if action in ("enter", "exit", "note"):
        validate_decision(record)          # the floor underneath (art. 28b)
    if action == "enter":
        _validate_enter(record, ctx)
    elif action == "exit":
        _validate_exit(record)
    elif action == "grade":
        _validate_grade(record)
    elif action == "disposition":
        _validate_disposition(record)
    elif action != "note":
        raise SchemaError(
            f"action must be enter|exit|note|grade|disposition, got {action!r}")
    return record


def append_record(record: dict, ctx: EntryContext | None = None,
                  path: str = "cache/proteus_journal.jsonl") -> None:
    """Validated, append-only write for the v2 journal. No edit, no delete."""
    import json
    import os

    validate_record(record, ctx)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
