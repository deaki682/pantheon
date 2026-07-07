"""shared/read_cascade.py — the comprehensive-reading machine (2026-07-07).

ONE harness, parameterized by `(universe, lens, budget)`, that both Oracle and
Proteus call. It replaces the thing that made those gods untestable: a no-edge
numeric filter that applied the expensive read to an arbitrary sliver. Here the
FILTER IS A READ — a cheap tier reads the whole field with high recall, and only
the survivors reach the expensive tier + the god's adversarial gate. No name is
ever dropped by a coin flip; every name is read, or recorded with the reason it
was not (budget), so the coverage is honest and the downstream A/B is honest.

THE ONE DESIGN CHOICE that makes all of this free to test: the model is an
INJECTED dependency (`model_read`), not a hardcoded call. In production it fans
out real Sonnet/Opus reads; in tests you pass a stub that returns canned outputs,
and the entire cascade — routing, budget cap, gating, coverage — runs end-to-end
with ZERO tokens. A harness bug can never cost a real run; credits go only to the
one thing that needs them (measuring whether the read has edge), on a small
sample, behind a go/no-go.

Vocabulary:
  - packet   : the evidence unit for one name (see `build_packet`), a plain dict.
  - Tier     : one read pass — its brain (model+effort), the prompt it sends, how
               to parse the raw model output into a verdict, and the keep predicate
               that decides who advances. Cheap triage first, expensive deep read
               (which runs the god's gate) second.
  - Lens     : an ordered list of Tiers — the god's identity (Oracle's inflection
               read + BEAR gate; Proteus's detective read + investigation gate).
  - model_read(reqs) -> raw outputs : THE injected seam. reqs is a list of
               {symbol, prompt, model, effort}; it returns one raw output per req,
               same order. Production fans out agents; tests return stubs.

Determinism: given a `model_read`, `run_cascade` is fully deterministic — same
packets + same stubbed reads → same result. That is what the test suite exploits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# --- the injected seam + the per-tier hooks (all god-supplied) ---------------
PromptFn = Callable[[dict], str]                 # packet -> prompt string
ParseFn = Callable[[Any, dict], dict]            # (raw_model_output, packet) -> verdict dict
KeepPred = Callable[[dict, dict], bool]          # (packet, verdict) -> advance?
ModelRead = Callable[[list], list]               # (reqs) -> raw outputs, SAME ORDER

TOKENS_KEY = "_tokens"                            # optional actual-token count a verdict may carry


def _identity_parse(raw: Any, packet: dict) -> dict:
    """Default parse: the raw model output already IS the verdict dict."""
    return raw if isinstance(raw, dict) else {"raw": raw}


@dataclass
class Tier:
    """One read pass in the cascade."""
    name: str                       # "triage" | "deep" (must be unique within a lens)
    model: str                      # 'haiku' | 'sonnet' | 'opus' (the tier's brain)
    effort: str                     # 'low' | 'medium' | 'high'
    prompt: PromptFn                # packet -> the read prompt
    keep: KeepPred                  # (packet, verdict) -> does it advance?
    parse: ParseFn = _identity_parse  # raw model output -> verdict (deep tier runs the gate here)
    est_tokens: int = 3000          # per-read estimate — used for BUDGETING and the dry-run


@dataclass
class Lens:
    """A god's read identity: the ordered tiers (cheap triage -> expensive deep)."""
    name: str
    tiers: list                     # list[Tier]


@dataclass
class Dropped:
    symbol: str
    tier: str
    reason: str


@dataclass
class CascadeResult:
    survivors: list                 # packets that cleared every tier, each carrying its verdicts
    dropped: list                   # list[Dropped] — killed on merit by a tier's keep predicate
    skipped_for_budget: list        # symbols never read because the budget ran out (NOT silent)
    coverage: dict                  # per-tier {read, advanced, dropped, skipped_budget}
    spent_tokens: int
    budget_tokens: int
    budget_hit: bool                # True iff any name was skipped for budget

    def summary(self) -> dict:
        return {"n_survivors": len(self.survivors), "n_dropped": len(self.dropped),
                "n_skipped_budget": len(self.skipped_for_budget),
                "spent_tokens": self.spent_tokens, "budget_tokens": self.budget_tokens,
                "budget_hit": self.budget_hit, "coverage": self.coverage}


def run_cascade(packets: list, lens: Lens, model_read: ModelRead, *,
                budget_tokens: int) -> CascadeResult:
    """Run `packets` through `lens`'s tiers under a hard token `budget`.

    Each tier reads as many of its inputs as the remaining budget affords (ordered
    as received — callers pass the most-promising first), advances the ones its
    keep predicate accepts, and records the rest. Names it could not afford to read
    are logged in `skipped_for_budget` — NEVER silently dropped, because a silent
    truncation reads as 'covered the field' when it didn't. Returns the survivors
    (with their per-tier verdicts attached) plus a full coverage/spend report.
    """
    # dedup by symbol, preserving order (a name must never be read twice)
    seen: set = set()
    current: list = []
    for p in packets:
        s = str(p.get("symbol", "")).upper()
        if s and s not in seen:
            seen.add(s)
            current.append(p)

    dropped: list = []
    skipped_for_budget: list = []
    coverage: dict = {}
    spent = 0
    budget_hit = False

    for tier in lens.tiers:
        remaining = budget_tokens - spent
        if tier.est_tokens > 0:
            affordable = max(0, remaining // tier.est_tokens)
        else:
            affordable = len(current)
        to_read = current[:affordable]
        skipped = current[affordable:]
        for p in skipped:
            skipped_for_budget.append(str(p.get("symbol", "")).upper())
        if skipped:
            budget_hit = True

        reqs = [{"symbol": str(p.get("symbol", "")).upper(), "prompt": tier.prompt(p),
                 "model": tier.model, "effort": tier.effort} for p in to_read]
        raws = model_read(reqs) if reqs else []
        if len(raws) != len(to_read):
            raise ValueError(f"model_read returned {len(raws)} outputs for {len(to_read)} "
                             f"requests in tier {tier.name!r} — must be 1:1 and in order")

        advanced: list = []
        for p, raw in zip(to_read, raws):
            verdict = tier.parse(raw, p)
            spent += int(verdict.get(TOKENS_KEY, tier.est_tokens))
            if tier.keep(p, verdict):
                advanced.append({**p, f"{tier.name}_verdict": verdict})
            else:
                dropped.append(Dropped(str(p.get("symbol", "")).upper(), tier.name,
                                       str(verdict.get("reason", ""))[:200]))
        coverage[tier.name] = {"read": len(to_read), "advanced": len(advanced),
                               "dropped": len(to_read) - len(advanced), "skipped_budget": len(skipped)}
        current = advanced

    return CascadeResult(survivors=current, dropped=dropped,
                         skipped_for_budget=skipped_for_budget, coverage=coverage,
                         spent_tokens=spent, budget_tokens=budget_tokens, budget_hit=budget_hit)


def estimate_cost(n_packets: int, lens: Lens, *, keep_rate: float = 0.4,
                  price_per_1k_tokens: Optional[float] = None) -> dict:
    """DRY-RUN cost, no model touched. Projects reads down the cascade assuming
    each tier advances `keep_rate` of what it read, and reports est tokens (and $,
    if a price is given) per tier and total — so you size a run and see the bill
    BEFORE spending a credit. Deliberately simple and slightly conservative."""
    per_tier: list = []
    total = 0
    cur = int(n_packets)
    for tier in lens.tiers:
        toks = cur * tier.est_tokens
        per_tier.append({"tier": tier.name, "model": tier.model, "reads": cur, "est_tokens": toks})
        total += toks
        cur = max(0, int(cur * keep_rate))
    out = {"n_packets": n_packets, "keep_rate": keep_rate, "per_tier": per_tier,
           "est_total_tokens": total}
    if price_per_1k_tokens is not None:
        out["est_cost_usd"] = round(total / 1000.0 * price_per_1k_tokens, 2)
    return out


# --- the evidence packet (pure assembler — no network, so it's unit-testable) --
def build_packet(*, symbol: str, name: str = "", sector: str = "", industry: str = "",
                 mcap_musd: Optional[float] = None, revenue_trajectory: Optional[list] = None,
                 margin_trajectory: Optional[list] = None, recent_trend_pct: Optional[float] = None,
                 range_pos_pct: Optional[float] = None, net_cash_ratio_pct: Optional[float] = None,
                 description: str = "", filing_snippet: str = "", **extra) -> dict:
    """Assemble one name's evidence packet — the compact, structured unit a tier
    reads. Pure: the data-fetch (Sharadar/EDGAR/Robinhood) is a separate layer, so
    this function — and everything built on it — is testable with fixtures. `extra`
    lets a lens attach god-specific fields (events, tags) without changing this."""
    pkt = {
        "symbol": str(symbol).upper(), "name": name, "sector": sector, "industry": industry,
        "mcap_musd": mcap_musd, "revenue_trajectory": revenue_trajectory or [],
        "margin_trajectory": margin_trajectory or [], "recent_trend_pct": recent_trend_pct,
        "range_pos_pct": range_pos_pct, "net_cash_ratio_pct": net_cash_ratio_pct,
        "description": description, "filing_snippet": filing_snippet,
    }
    pkt.update(extra)
    return pkt
