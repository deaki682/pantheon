# /buzz — weekly retail-acceleration bet (paper/ghost-first)

The candidate replacement for convergence-Midas. Finds small/mid-caps where
retail talk is **accelerating** (not just loud), confirmed by real price/volume
so it's organic money and not a pump, then a **serious-thinking LLM pass** reads
the actual chatter and recommends the top names with inspectable reasoning.

**Hard rules (non-negotiable):**
- **Paper/ghost only in v1.** NEVER places a live order. No sleeve, no ledger.
- Disconnected — imports nothing from oracle/midas/delphi/achilles; own cache
  namespace (`cache/buzz_*.json`); never persists to a god's state.
- The mechanical gates decide *what qualifies*. The LLM recommends *from the
  qualified set only* — it never invents a ticker and never overrides a failed
  price/volume gate with vibes.
- The edge is a slight, diversified one. Basket, never one name. Prove it in the
  ghost before anyone discusses real capital.

## Steps

### Mechanical layer — what qualifies (no judgment yet)

1. **Fetch buzz.** `curl` ApeWisdom pages (`https://apewisdom.io/api/v1.0/filter/all-stocks/page/N`,
   ~9 pages). It returns `mentions` and `mentions_24h_ago` per ticker — acceleration
   for free, no auth/NLP. `buzz.acceleration.parse_apewisdom(payload)` →
   `accelerating(rows)` keeps only names igniting vs their own baseline (drops the
   loud-but-fading "level trap" like MU/SPY/MSFT).

2. **Small/mid filter + price/volume confirmation.** For each accelerating name:
   - Market cap via `get_equity_fundamentals`. Keep only `buzz.scanner.in_small_mid_band`
     ($50M–$10B) — buzz is noise on mega-caps, untradeable on microcaps.
   - Daily historicals via `get_equity_historicals` (~30 bars). `buzz.confirm.confirm(bars)`
     → is price rising AND volume elevated? This is the **direction + anti-manipulation
     gate**: talk with no price/volume behind it is astroturf — skip it.
   - `buzz.scanner.build_candidate(sig, market_cap, conf)`.

3. **Rank the basket.** `buzz.scanner.rank_basket(candidates, top_n=8)` — confirmed
   small/mid accelerators, hottest first. This is the qualified set.

### Serious-thinking LLM layer — recommend from the qualified set

4. **Read what's actually being said.** For each qualified candidate, gather real
   context (do NOT skip this — it's the whole point):
   - The actual chatter: `curl` the StockTwits stream
     (`https://api.stocktwits.com/api/2/streams/symbol/{TICKER}.json`) — what are
     people saying, and is the sentiment on a second platform or isolated to Reddit?
   - Recent news / 8-K filings (EDGAR) — is there a real catalyst behind the talk?
   - **Insider corroboration** (the best anti-pump tell): check recent Form 4 open-
     market buys (`oracle.lenses.search_recent_form4` is available, but treat this as
     an external read — do not import god *state*). Insiders don't buy to help a pump.

5. **Judge each name — think hard and skeptically (use adaptive/extended thinking).**
   For every candidate produce a structured judgment:
   - `authenticity`: organic accelerating interest vs a coordinated pump. Weigh:
     does price/volume confirm? is it on two platforms? insider buying? real
     catalyst? one-sided ramp language and burst posting = pump smell.
   - `direction`: bull / bear / unclear. Accelerating talk on *bad* news (dilution,
     fraud, going concern going viral) is a short, not a long — say so and drop it.
   - `catalyst`: the specific reason it's igniting this week.
   - `key_risk`: what kills it (reversal after the pop, dilution, the pump unwinding).
   - `confidence`: honest 0–1.
   - `recommend`: true only if authentic + bullish direction + real catalyst.

6. **Recommend the top names** (typically 3–5) with a written thesis each. Rank by
   your judgment among the *mechanically qualified* set — you may veto/deprioritize,
   you may NOT promote a name that failed the price/volume gate. Save to
   `cache/buzz_shortlist.json` and print the recommendations with reasoning.

### Ghost — validate before trusting any of this

7. **Shadow everything.** Hand the accelerating candidates (confirmed AND
   unconfirmed) to `buzz.ghost.candidates_to_ghost(candidates, price_lookup,
   recommended=<LLM picks from step 6>, insider_backed=<insider set from step 4>)`,
   then `buzz.ghost.open_entries(...)` at a 5-day horizon. The `recommended` and
   `insider_backed` sets are what make the LLM and insider layers testable — pass
   them through. Full ghost run lives in **`/buzz-ghost`**.

8. **Measure whether each layer earns its place.** `buzz.ghost.buzz_report(ledger)`
   → `signal_lift` answers all three at once: do **confirmed** names beat
   unconfirmed (price/volume gate)? do **llm_recommended** names beat the reviewed
   names it passed on (is the thinking real or theater)? do **insider_backed**
   names beat the rest (authenticity gate)? Plus `accel_terciles`: does more
   acceleration predict more return? Keep only the layers the ghost proves add
   lift — exactly the check convergence-Midas never ran.

## Deliberately NOT built yet
- No live sleeve / orders. v1 is a shortlist + ghost. Promotion to real capital
  (and inheriting the Midas name/sleeve) waits on the ghost showing an edge net of
  costs — costs are brutal on small-caps, so watch slippage.
- No stacked convergence score. Extra signals (insider, short float, catalyst) enter
  only as *gates the ghost validates*, one at a time — never a tuned multi-channel
  score. That blend is the overfitting trap that sank the old Midas.

## Why disconnected / why paper-first
It's an unproven hypothesis on the most adversarial data we touch (retail buzz is
actively manipulated). Isolating it means a bug can't hit a god's sleeve, and the
ghost can kill the idea cheaply if the edge isn't real — the correct, profitable
outcome if it doesn't work.
