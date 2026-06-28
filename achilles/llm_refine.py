"""LLM-powered filing analysis for Achilles.

Reads SEC 8-K bodies and extracts trading signals that regex can't:
  - Is the earnings beat genuine (operations) or noise (one-time items)?
  - Management tone: confident, cautious, or hedging?
  - Concurrent catalysts: buyback, new contract, raised guidance?
  - Red flags: restatement, going concern, auditor change?

The LLM provides information-processing speed — understanding the filing
faster and deeper than the market can reprice it. This is the edge that
can't show up in a backtest.

Requires ANTHROPIC_API_KEY in environment. Falls back gracefully to
neutral signals when unavailable.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger("achilles.llm_refine")

MODEL = "claude-sonnet-4-6"
MAX_BODY_CHARS = 12_000
TIMEOUT_SECONDS = 15

SYSTEM_PROMPT = """\
You are a quantitative trading analyst reading SEC 8-K filings for a \
small-cap event-driven strategy focused on Post-Earnings Announcement \
Drift (PEAD). Your job is to extract structured signals from the filing \
text that predict whether the stock will drift higher over the next \
30-45 days.

You are NOT making a buy/sell recommendation. You are extracting \
factual signals from the text. Be precise and conservative — only flag \
what the text explicitly states."""

ANALYSIS_PROMPT = """\
Analyze this 8-K filing for {symbol} (earnings event, {surprise_desc}).

Extract these signals from the filing text:

1. BEAT QUALITY: Is the earnings beat driven by core operations \
(revenue growth, margin expansion) or by one-time items (asset sales, \
tax benefits, litigation settlements, accounting changes)? Answer \
"genuine", "mixed", or "one_time".

2. MANAGEMENT TONE: From any forward-looking statements, management \
discussion, or press release language, rate the tone as "confident" \
(raised outlook, strong pipeline), "neutral" (reiterated, no change), \
or "cautious" (hedging language, uncertainty, macro concerns).

3. CONCURRENT CATALYSTS: List any additional positive catalysts \
mentioned alongside earnings: share buyback announced, dividend \
increase, new contract/partnership, acquisition, guidance raised, \
debt reduction, insider purchases disclosed.

4. RED FLAGS: List any negatives: going concern language, auditor \
change, restatement, material weakness, goodwill impairment, \
restructuring charges, executive departure, SEC investigation, \
delayed filing.

5. REVENUE SIGNAL: Did revenue beat or miss expectations, or is it \
not mentioned? Answer "beat", "miss", "inline", or "unknown". Revenue \
beats with EPS beats produce stronger PEAD than EPS-only beats.

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "beat_quality": "genuine" | "mixed" | "one_time",
  "management_tone": "confident" | "neutral" | "cautious",
  "catalysts": ["list", "of", "catalysts"],
  "red_flags": ["list", "of", "flags"],
  "revenue_signal": "beat" | "miss" | "inline" | "unknown",
  "one_line_summary": "brief factual summary of what the filing says"
}}

Filing text:
{body}"""


@dataclass
class LLMSignals:
    beat_quality: str = "unknown"
    management_tone: str = "neutral"
    catalysts: list[str] = None
    red_flags: list[str] = None
    revenue_signal: str = "unknown"
    summary: str = ""
    raw_response: str = ""

    def __post_init__(self):
        if self.catalysts is None:
            self.catalysts = []
        if self.red_flags is None:
            self.red_flags = []

    @property
    def strength_adjustment(self) -> float:
        """Convert LLM signals into a multiplicative strength adjustment.

        This is conservative by design — the LLM should help avoid bad
        trades more than it boosts good ones.
        """
        adj = 1.0

        if self.beat_quality == "one_time":
            adj *= 0.4
        elif self.beat_quality == "mixed":
            adj *= 0.7

        if self.management_tone == "confident":
            adj *= 1.15
        elif self.management_tone == "cautious":
            adj *= 0.85

        if self.revenue_signal == "beat":
            adj *= 1.10
        elif self.revenue_signal == "miss":
            adj *= 0.75

        if self.red_flags:
            adj *= max(0.3, 1.0 - 0.15 * len(self.red_flags))

        if self.catalysts:
            adj *= min(1.3, 1.0 + 0.08 * len(self.catalysts))

        return round(adj, 3)

    @property
    def disqualifiers(self) -> list[str]:
        """Extract hard disqualifiers from red flags."""
        hard_flags = {
            "going concern", "restatement", "material weakness",
            "sec investigation", "auditor change",
        }
        return [f for f in self.red_flags if f.lower() in hard_flags]

    def to_dict(self) -> dict:
        return {
            "beat_quality": self.beat_quality,
            "management_tone": self.management_tone,
            "catalysts": self.catalysts,
            "red_flags": self.red_flags,
            "revenue_signal": self.revenue_signal,
            "summary": self.summary,
            "strength_adjustment": self.strength_adjustment,
        }


def _neutral() -> LLMSignals:
    return LLMSignals()


def analyze_filing(
    body_text: str,
    symbol: str,
    surprise_pct: Optional[float] = None,
) -> LLMSignals:
    """Analyze an 8-K filing body with the LLM.

    Returns LLMSignals with extracted trading signals. Falls back to
    neutral signals if the API key is missing, the call fails, or the
    body is too short to be useful.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.debug("No ANTHROPIC_API_KEY — skipping LLM analysis")
        return _neutral()

    if not body_text or len(body_text.strip()) < 200:
        log.debug("Filing body too short for LLM analysis (%d chars)", len(body_text or ""))
        return _neutral()

    truncated = body_text[:MAX_BODY_CHARS]

    if surprise_pct is not None:
        surprise_desc = f"EPS surprise {surprise_pct:+.1f}%"
    else:
        surprise_desc = "surprise % unknown"

    prompt = ANALYSIS_PROMPT.format(
        symbol=symbol,
        surprise_desc=surprise_desc,
        body=truncated,
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS)
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as exc:
        log.warning("LLM call failed for %s: %s", symbol, exc)
        return _neutral()

    return _parse_response(raw)


def _parse_response(raw: str) -> LLMSignals:
    """Parse the LLM JSON response into LLMSignals."""
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean
            clean = clean.rsplit("```", 1)[0]
        data = json.loads(clean)
    except (json.JSONDecodeError, IndexError):
        log.warning("Failed to parse LLM response: %s", raw[:200])
        return LLMSignals(raw_response=raw)

    return LLMSignals(
        beat_quality=data.get("beat_quality", "unknown"),
        management_tone=data.get("management_tone", "neutral"),
        catalysts=data.get("catalysts", []),
        red_flags=data.get("red_flags", []),
        revenue_signal=data.get("revenue_signal", "unknown"),
        summary=data.get("one_line_summary", ""),
        raw_response=raw,
    )


# ── Guidance revision analysis ────────────────────────────────────────

GUIDANCE_SYSTEM_PROMPT = """\
You are a quantitative trading analyst reading SEC 8-K filings for a \
small-cap event-driven strategy. Your job is to extract structured \
signals from guidance revision filings that predict whether the stock \
will drift higher over the next 5-10 days.

You are NOT making a buy/sell recommendation. You are extracting \
factual signals from the text. Be precise and conservative — only flag \
what the text explicitly states."""

GUIDANCE_PROMPT = """\
Analyze this 8-K filing for {symbol} (guidance revision event).

Extract these signals from the filing text:

1. DIRECTION: Is guidance being "raised", "lowered", "initiated" \
(first-time guidance), "narrowed_up" (range narrowed toward upper end), \
"narrowed_down" (range narrowed toward lower end), or "withdrawn"?

2. METRIC: What financial metric is being guided? (e.g., "revenue", \
"eps", "ebitda", "operating_income", "free_cash_flow", "margin", "other")

3. MAGNITUDE: How significant is the change relative to the prior \
range or consensus? Rate 0.0-1.0:
  0.0 = trivial (<2% change)
  0.3 = modest (2-5%)
  0.6 = significant (5-15%)
  1.0 = dramatic (>15% or transformative)

4. SPECIFICITY: How concrete is the new guidance? Rate 0.0-1.0:
  0.0 = vague qualitative ("we expect improvement")
  0.5 = directional with context ("above prior range")
  1.0 = precise numeric ("$X.XX to $Y.YY EPS")

5. SURPRISE: Was this guidance change expected or a surprise? \
Rate 0.0-1.0:
  0.0 = pre-announced or widely expected
  0.5 = somewhat expected but timing/magnitude uncertain
  1.0 = complete surprise

6. PRIOR_RANGE: Quote the prior guidance range if mentioned.
7. NEW_RANGE: Quote the new guidance range.

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "direction": "raised" | "lowered" | "initiated" | "narrowed_up" | "narrowed_down" | "withdrawn",
  "metric": "revenue" | "eps" | "ebitda" | "operating_income" | "free_cash_flow" | "margin" | "other",
  "magnitude": 0.0,
  "specificity": 0.0,
  "surprise": 0.0,
  "prior_range": "",
  "new_range": "",
  "one_line_summary": "brief factual summary"
}}

Filing text:
{body}"""


LONG_DIRECTIONS = frozenset({"raised", "initiated", "narrowed_up"})


@dataclass
class GuidanceSignals:
    direction: str = "unknown"
    metric: str = "unknown"
    magnitude: float = 0.0
    specificity: float = 0.0
    surprise: float = 0.0
    prior_range: str = ""
    new_range: str = ""
    summary: str = ""
    raw_response: str = ""

    @property
    def strength_adjustment(self) -> float:
        """Strength for the guidance event.

        Returns 0.0 for untradeable directions (lowered, withdrawn,
        narrowed_down — can't go short). For tradeable directions,
        returns 0.3–1.3 based on magnitude (50%), surprise (30%),
        and specificity (20%).
        """
        if self.direction not in LONG_DIRECTIONS:
            return 0.0

        mag = max(0.0, min(1.0, self.magnitude))
        spec = max(0.0, min(1.0, self.specificity))
        surp = max(0.0, min(1.0, self.surprise))

        raw = 0.50 * mag + 0.30 * surp + 0.20 * spec
        strength = 0.3 + raw * 1.0

        if self.direction == "initiated":
            strength *= 0.85

        return round(strength, 3)

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "metric": self.metric,
            "magnitude": self.magnitude,
            "specificity": self.specificity,
            "surprise": self.surprise,
            "prior_range": self.prior_range,
            "new_range": self.new_range,
            "summary": self.summary,
            "strength_adjustment": self.strength_adjustment,
        }


def _neutral_guidance() -> GuidanceSignals:
    return GuidanceSignals()


def analyze_guidance_filing(
    body_text: str,
    symbol: str,
) -> GuidanceSignals:
    """Analyze a guidance 8-K filing body with the LLM.

    Falls back to neutral signals when the API key is missing or the
    call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.debug("No ANTHROPIC_API_KEY — skipping guidance LLM analysis")
        return _neutral_guidance()

    if not body_text or len(body_text.strip()) < 200:
        log.debug("Filing body too short for guidance analysis (%d chars)",
                  len(body_text or ""))
        return _neutral_guidance()

    truncated = body_text[:MAX_BODY_CHARS]
    prompt = GUIDANCE_PROMPT.format(symbol=symbol, body=truncated)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS)
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=GUIDANCE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as exc:
        log.warning("Guidance LLM call failed for %s: %s", symbol, exc)
        return _neutral_guidance()

    return _parse_guidance_response(raw)


def _parse_guidance_response(raw: str) -> GuidanceSignals:
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean
            clean = clean.rsplit("```", 1)[0]
        data = json.loads(clean)
    except (json.JSONDecodeError, IndexError):
        log.warning("Failed to parse guidance LLM response: %s", raw[:200])
        return GuidanceSignals(raw_response=raw)

    return GuidanceSignals(
        direction=data.get("direction", "unknown"),
        metric=data.get("metric", "unknown"),
        magnitude=float(data.get("magnitude", 0.0)),
        specificity=float(data.get("specificity", 0.0)),
        surprise=float(data.get("surprise", 0.0)),
        prior_range=data.get("prior_range", ""),
        new_range=data.get("new_range", ""),
        summary=data.get("one_line_summary", ""),
        raw_response=raw,
    )
