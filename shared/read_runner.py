"""shared/read_runner.py — the SESSION-DRIVEN cascade (the production read path).

`run_cascade` takes an injected `model_read` and runs the whole cascade in one
process — perfect for tests (stub reader) and any in-process API reader. But in
production the reads are done by the SESSION: for a big tier the session fans the
prompts out to subagents (Workflow), which a synchronous Python callable cannot
do. So production needs to run the cascade STEPWISE:

    runner = CascadeRunner(packets, lens, budget_tokens=BUDGET)
    while not runner.done:
        batch = runner.next_batch()          # the tier's requests (prompts + model)
        raws  = <session fans `batch['reqs']` out to agents, collects raw outputs>
        runner.submit(raws)                  # parse + gate + advance
    result = runner.result()                 # identical CascadeResult to run_cascade

The runner shares `plan_tier`/`apply_tier` with `run_cascade`, so the two paths
can NOT diverge on budget, coverage, dedup, or gating — only on WHO performs the
reads. Between `next_batch()` and `submit()` the session is free to spend real
credits (a Workflow fan-out); everything the runner itself does is free.

`write_batch`/`read_answers` are the thin file contract for handing a batch to a
Workflow and reading its answers back. `dict_reader` builds a `model_read` from a
pre-collected {symbol: raw} map — the bridge for a penny smoke test where the
session already has the handful of reads in hand.
"""
from __future__ import annotations

import json

from shared.read_cascade import (
    CascadeResult,
    Lens,
    apply_tier,
    dedup_packets,
    plan_tier,
)


class CascadeRunner:
    """Stepwise driver: hand out one tier's requests, take back its raw outputs,
    advance. Same arithmetic as `run_cascade`, but the session performs the reads
    in between — so a tier can be fanned out to subagents."""

    def __init__(self, packets: list, lens: Lens, *, budget_tokens: int):
        self.lens = lens
        self.budget_tokens = int(budget_tokens)
        self._current = dedup_packets(packets)
        self._tier_i = 0
        self._spent = 0
        self._dropped: list = []
        self._skipped: list = []
        self._coverage: dict = {}
        self._budget_hit = False
        self._pending = None            # (tier, to_read, n_skipped) awaiting submit()

    @property
    def done(self) -> bool:
        return self._pending is None and self._tier_i >= len(self.lens.tiers)

    def _record_skips(self, tier, skipped):
        for p in skipped:
            self._skipped.append(str(p.get("symbol", "")).upper())
        if skipped:
            self._budget_hit = True

    def next_batch(self):
        """Return the next tier's read requests, or None when the cascade is done.
        Tiers that need no model call (nothing survived, or budget affords nothing)
        are applied automatically here — the session only ever sees batches that
        actually require reads, and can't accidentally skip the budget/coverage
        bookkeeping for the empty ones."""
        if self._pending is not None:
            raise RuntimeError("submit() the outstanding batch before requesting the next")
        while self._tier_i < len(self.lens.tiers):
            tier = self.lens.tiers[self._tier_i]
            plan = plan_tier(self._current, tier, self.budget_tokens - self._spent)
            self._record_skips(tier, plan["skipped"])
            if plan["reqs"]:
                self._pending = (tier, plan["to_read"], len(plan["skipped"]))
                return {"tier": tier.name, "model": tier.model, "effort": tier.effort,
                        "reqs": plan["reqs"], "n_to_read": len(plan["to_read"]),
                        "n_skipped_budget": len(plan["skipped"])}
            # no reads needed: apply the empty tier, record coverage, advance
            self._apply(tier, [], [], len(plan["skipped"]))
            self._tier_i += 1
        return None

    def _apply(self, tier, to_read, raws, n_skipped):
        applied = apply_tier(tier, to_read, raws)
        self._dropped.extend(applied["dropped"])
        self._spent += applied["spent"]
        cov = applied["coverage"]
        cov["skipped_budget"] = n_skipped
        self._coverage[tier.name] = cov
        self._current = applied["advanced"]

    def submit(self, raws: list):
        """Feed the raw model outputs for the outstanding batch (1:1, in request
        order) back in; the tier is parsed, gated, and advanced."""
        if self._pending is None:
            raise RuntimeError("no outstanding batch — call next_batch() first")
        tier, to_read, n_skipped = self._pending
        self._pending = None
        self._apply(tier, to_read, raws, n_skipped)
        self._tier_i += 1

    def result(self) -> CascadeResult:
        if not self.done:
            raise RuntimeError("cascade not finished — keep calling next_batch()/submit()")
        return CascadeResult(
            survivors=self._current, dropped=self._dropped,
            skipped_for_budget=self._skipped, coverage=self._coverage,
            spent_tokens=self._spent, budget_tokens=self.budget_tokens,
            budget_hit=self._budget_hit)


# --- the file contract for a Workflow handoff -------------------------------
def write_batch(path: str, batch: dict) -> str:
    """Persist a batch (from `next_batch()`) so a Workflow / out-of-process fan-out
    can pick up its `reqs`. Returns the path."""
    json.dump(batch, open(path, "w"))
    return path


def read_answers(path: str) -> list:
    """Read a fan-out's raw outputs back. Accepts either a bare JSON list, or an
    object with an `answers` list (so a Workflow can attach metadata alongside)."""
    obj = json.load(open(path))
    if isinstance(obj, dict) and "answers" in obj:
        return obj["answers"]
    if isinstance(obj, list):
        return obj
    raise ValueError(f"{path}: expected a list of answers or {{'answers': [...]}}")


# --- in-process bridge for a small penny run --------------------------------
def dict_reader(answers_by_symbol: dict):
    """Build a `model_read` from a pre-collected {SYMBOL: raw} map — the bridge for
    a penny smoke test where the session already holds the handful of reads. Raises
    on a missing symbol (a silent default would corrupt the gate)."""
    def _read(reqs: list) -> list:
        out = []
        for r in reqs:
            sym = str(r.get("symbol", "")).upper()
            if sym not in answers_by_symbol:
                raise KeyError(f"no read supplied for {sym} (tier {r.get('model')})")
            out.append(answers_by_symbol[sym])
        return out
    return _read
