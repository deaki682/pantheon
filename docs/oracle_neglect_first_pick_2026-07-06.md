# Oracle neglect leg → first verified pick: INVE (2026-07-06)

The neglect leg's first end-to-end run: coverage → precision-stage triage →
primary-source verification → a verified, fundable dossier. Proof the three-leg
machine drives to a *pick*, not a list.

## Triage (323 below-floor names → 33 → 1 verified)

The neglect screen surfaced 323 below-floor names. Precision triage narrowed to
the strongest convex shape — **below net cash, non-eroding, US-domiciled** (33
names), ranked by discount. The purest sub-set is below net cash AND
cash-generative (FBIO, MED, MYPS); the deepest hard discount was **INVE
(Identiv)** at a headline 49% below net cash.

Trap flagged, not verified: **FBIO (Fortress Biotech)** shows ~$203M "net cash"
but is a holding company with partially-owned subsidiaries and a one-time
deconsolidation gain — the consolidated cash is not attributable to common
(minority interests). Left as *flagged* (a verification-gate kill candidate),
not claimed as a confirmed kill without the 10-Q read.

## INVE — verified against the 2026-03-31 10-Q (accession 0001193125-26-223705)

| Fact (primary source) | Value |
|---|---|
| Cash & equivalents | $124.525M |
| Total debt / credit facilities | **$0** |
| Total liabilities (all operating: AP, leases, accruals) | $10.482M |
| Goodwill / intangibles | $0 |
| Noncontrolling interests | none (wholly-owned subs) |
| Common outstanding (2026-05-04) | 24,006,212 |
| Series B preferred, as-converted | 7,126,723 (pari-passu participating equity) |
| Net-of-**all**-liabilities cash | ~$114.0M |
| Fully-diluted shares | ~31.13M |
| Net cash per FD share | **$3.66** |
| Live price (2026-07-06 pre-mkt) | **$2.61** |
| Discount to net cash (fully diluted) | **~29%** |

**What verification changed.** The screen's headline was "49% below net cash"
(net cash $124M vs $63M cap). The primary-source read corrects it to **~29%**
once the 7.13M as-converted Series B dilution is included — a material haircut the
fundamentals snapshot could not see. This is the LLM-lift the A/B measures: the
read moved the number.

**The four traps — all pass on FLOOR integrity:**
- `debt_reconciled_full_stack` ✓ — read the full liability stack ($10.5M, all
  operating, zero debt). The XRN trap (a missed credit facility) cannot fire here.
- `book_survives_goodwill` ✓ — no goodwill; tangible book = total equity.
- `floor_not_merely_asserted` ✓ — floor_basis `net_net` (countable cash net of
  every liability), not an activist's appraisal.
- `catalyst_not_already_fired` ✓ — stock near multi-year lows, no pop.
- `primary_source_cited` ✓ — the 10-Q itself.

Result: `convex=True`, `verified=True`, `is_fundable=True`, floor re-stamped
**hard** (net_net basis), convexity_score 0.083.

## The honest caveat — a hard floor, a soft catalyst

The four traps certify FLOOR integrity, not catalyst strength. INVE's catalyst is
**undated** (structural neglect of a post-divestiture cash box): a $10M
repurchase authorization (modest vs a $63M cap), potential larger capital return,
accretive redeployment, or an activist — none dated. The operating stub loses
~$14M/yr, slowly melting the floor (still 40+ quarters of runway). So this is a
**bounded-floor position, not a top-conviction catalyst bet** — size accordingly.
Kill: a 10-Q showing net cash per FD share < $3.00, or a >$40M unrelated
acquisition. The dossier records this explicitly.

## Recorded

- `cache/oracle_convex_dossiers.json` — INVE added (pool now JOF + INVE),
  persisted to `claude/live`.
- `cache/oracle_ab.json` — INVE logged as a fresh-launch A/B selection
  (arm A LLM + arm B screen; the note records the 49%→29% correction).

Oracle now has **two** verified fresh-launch names — JOF (forced-seller /
CEF sub-NAV) and INVE (neglect / sub-net-cash cash box) — one from each of two
different legs, both cleared by the same four-trap gate. Still `pending_funding`
(research/paper until the sleeve is funded).

## The other side of the gate — MED (Medifast) REJECTED as a screen false-positive

Same run, opposite outcome — the discipline working both ways. The screen ranked
MED "20% below net cash" (net_cash $153M vs $122M cap). The primary-source read
(10-Q, 2026-03-31, accession 0001628280-26-029898) dissolved it:

- The screen's `debt=$16M` is **operating lease obligations, not debt** — MED has
  ZERO real borrowings (no revolver, no term loan). Sharadar's `debt` field folds
  in capitalized leases.
- Cash + current investments = $168.9M, but total liabilities are **$54.4M**
  (incl. $38.3M payables/accruals a going-concern must pay). Net of all
  liabilities ≈ $114.5M / 11.12M sh = **$10.30/sh** — versus an $11.01 price. The
  stock trades *slightly ABOVE* its conservative net-cash floor, not below it.
- Unlike INVE (a $124.5M cash box, $10.5M liabilities, a tiny stub), MED is a
  **going concern in GLP-1-driven structural decline** whose cash funds real
  working capital and could be consumed if OPTAVIA keeps shrinking into cash burn.

Verdict: **not fundable** — no hard-floor margin of safety once operating
liabilities are properly netted; the headline discount was an artifact of
mislabeling leases as debt and ignoring payables. Recorded as a triage kill, not
added to the pool. (The same shape to watch for across the tangible_book tail:
Sharadar `debt` includes leases, so the screen slightly overstates net cash for
lease-heavy operators — a known coverage-stage generosity the precision read
corrects, name by name.)

## Net of the run

Two names entered the gate from the neglect leg; **one cleared** (INVE — a hard,
verified, debt-free floor with real margin of safety) and **one was rejected**
(MED — a soft going-concern floor at ~par). That 1-for-2 is the machine behaving
correctly: coverage is generous, the primary-source read is what turns a ranked
list into a funded decision — and it says NO as readily as YES.
