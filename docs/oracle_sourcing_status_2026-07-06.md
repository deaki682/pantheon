# Oracle forced-seller sourcing — status (2026-07-06)

The coverage half of the Oracle rebuild. Fixes the bottleneck the launch gate
exposed: the four lenses (insider/13F/13D/quality) are a narrow, biased net with
~zero measured mechanical alpha that miss most of the universe. The durable
convex edges live in **structural forced-seller events**, which leave a filing
trail and are findable exhaustively. `oracle/forced_seller_sourcing.py`
generalizes the proven `nemesis.spinoffs` scanner into a multi-family EDGAR
full-text sweep, graveyard-excluded and Hermes-deduped, feeding the
`make_convex_dossier → verify_dossier → rank_fundable` precision stage.

## First live sweep (2026-05-01 .. 2026-07-06)

26 NEW candidates surfaced across the whole EDGAR universe — names the lenses
would never have flagged. Precision-stage triage yield:

| Bucket | n | Disposition |
|---|---|---|
| **Real, tradable, convex CEF** | **1** | **JOF** — the one genuine prize |
| Non-traded / private funds (real events, un-actionable) | 11 | GPB×2, Ares×4, Franklin, Hancock, Crescent, Priority, Vista — drop |
| Operating-company keyword false positives | ~9 | PBI, TSEOF, NOTV, VREOD, ISBA, ARI, SGMO, HTT, OPTU |
| Real operating distress, NO hard floor | 4 | ORGN (projected-to-zero), SNBR (Ch.11), CRMT (near-BK), FABTQ (distressed-Q) |
| Spent tenders (window already closed) | 2 | EXFY (6/10), NHP-preferred (6/16) |

**Honest read:** real signal rate is low (1/26 actionable) but *structurally
correct* — the sweep fired on the right language and the verification discipline
burned off the 25 that don't clear the bar. That is the two-stage architecture
working: coverage widens, precision filters. 1 real lead the lenses could never
have found is 1 more than the old process produced, and the sweep compounds
weekly.

## The one real lead — JOF (Japan Smaller Capitalization Fund)

The exact archetype the engine is built to find: a listed, liquid closed-end
fund (Nomura-run, ~$11.70) at a **real, published ~10.5% discount to NAV** with a
**structural forced-seller mechanism** — a board policy that auto-triggers a
conditional tender at 98% of NAV whenever the average discount runs wide (>9%
over a measured window). Next stage: (a) pull current NAV vs price to confirm the
live post-tender discount, (b) read the N-CSR / tender 8-K for the *recurring*
discount-trigger terms (the recurrence is what makes it convex beyond one
window), (c) honest caveat — this cycle's tender expired 7/1/26 and prorated, so
the trade is the persistent-discount + next-trigger structure, not the spent
window. Floor basis = a published, audited NAV discount (a real floor, unlike
SMHI's asserted one); run it through `verify_dossier` before any position.

## Engine gaps to tighten (next build)

1. **Issuer-type filter (fund vs operating company).** The coarse full-text
   queries surface ~9 keyword false positives per sweep (operating companies
   whose 8-K merely contains "plan of liquidation"). A CEF/BDC/fund issuer gate
   (SIC code / form-type / registered-investment-company flag) drops them before
   they reach precision.
2. **Latency — catch commencement, not expiry.** The one prize (JOF) and the two
   real tenders (NHP, EXFY) were surfaced from filings whose windows had already
   closed by processing night. To capture CEF sub-NAV convexity, the sweep must
   catch the *commencement* filing (SC TO-I as filed) or the discount-trigger
   determination with days of runway — tighten the query/form set and run the
   sweep on a tighter cadence.

Both are tooling improvements that compound every future session — per the
standing posture, build the machine, not just the picks.

## MEASURED (2026-07-06): keyword search has 12% recall — switch Stage 1 to form-enumeration

Built the yardstick (`run_stage1_answerkey.py`): for June 2026, enumerated the
**definitionally-complete** set of two form-defined forced-seller families from
EDGAR's daily form indexes — every `SC TO-I` / `SC TO-I/A` (issuer tenders) and
`N-8F` (fund deregistrations), **92 distinct filers**, no keyword. Then scored
the current keyword sweep against it:

- **Keyword sweep recall = 12%** (caught 11 of 92; missed 81).
- The 81 misses include a large private-credit-BDC / interval-fund tender
  cluster (Barings, Goldman Sachs Private Credit, Blackstone Private Credit,
  First Eagle, Lord Abbett, Antares, Willow Tree, Crestline, …).

**Verdict — with a number, not a hunch:** rebuild Stage 1 around **form
enumeration** (daily form indexes → every filing of the forms that ARE the
events → 100% recall by construction), and move precision to a cheap **Stage-2
tradability filter** (most of the 81 are non-traded funds — the clean signal is
"does it have a live listed quote?"). Keyword full-text search is retained only
as a supplement for families with no single defining form (e.g. rights offerings
buried in S-1/424B prose). Answer key saved: `cache/oracle_stage1_answerkey.json`.

## LOOSEN -> MEASURE -> CORRECT (2026-07-06): the delisting channel is the wrong instrument

Loosened coverage (added Form 25/25-NSE "delisting", widened the window 2->3mo,
de-blunted the tradability filter). The wider sweep produced 124 tradable
(from 14) + 296 flagged. But on measuring the new delisting channel: of its 105
tradable hits, ~all were NOISE — 39 non-common securities (warrants/preferred/
bankruptcy-Q/units) and 66 "plain common" dominated by healthy mega-caps
(V/WMT/PEP/LLY/XOM/FDX, all trading normally) that filed a Form 25 to delist a
specific NOTE/WARRANT, not the company. Genuine whole-company exchange delistings
are distress or going-private — no floor, or Hermes's.

**Correction:** a Form 25 is NOT the index-DELETION forced-seller mechanic. A
solvent stock forced off an INDEX while it keeps trading is an S&P/Russell
index-provider announcement — a different data source (not EDGAR). The delisting
channel is DEMOTED (removed from form enumeration); index-deletion is future work
against index-reconstitution data. The kept wins from the loosening: the wider
window + N-8F ORDR fix grew the clean CEF/BDC tender leads to 7 (JOF, EVV, EFR,
EVF, PGIM, EIIA, FRBP), and the de-blunted tradability split preserves flagged
names instead of dropping them. Loosen -> measure -> correct, with a number.

## THREE-LEG COVERAGE COMPLETE (2026-07-06): neglect + hard_catalyst added

Fixed the architectural gap the fresh launch exposed: the sourcing net covered
only forced-seller EVENTS, so a name whose mispricing is structural NEGLECT (a
below-floor state with no filing to enumerate) or a HARD CATALYST (an activist
campaign / sale process) could never surface — yet 4 of 5 names Oracle liked
pre-rebuild (ARVN/VTSI/ALCO/RNA) were neglect theses. Coverage now spans all
three why_mispriced types the precision gate can fund, one leg each:

| Leg | Module | Method | First live pass |
|---|---|---|---|
| **forced_seller** | `oracle.forced_seller_sourcing` | EDGAR daily-index form enumeration (SC TO-I / N-8F / 10-12B) + tradability split | 21 tradable |
| **hard_catalyst** | `oracle.hard_catalyst_sourcing` | SC 13D / 13D-A form enumeration (each `requires_item4_read`) + strategic-review 8-K keyword supplement | 1 activist 13D + 13 strategic-review (EHAB/FWRD/ZYME/BTU/WY — real in-play names) |
| **neglect** | `oracle.neglect_screen` | whole Sharadar panel screened for price < countable floor | 323 below-floor names |

Unified in `run_oracle_sourcing.py` → one combined
`cache/oracle_sourced_candidates.json` (358 actionable candidates across the
three legs, first pass). Every candidate still faces the same
`make_convex_dossier → verify_dossier → rank_fundable` gate.

**The neglect screen — how it stays honest at the COVERAGE stage** (the precision
gate does the rest). Three floors per name from the latest SF1 balance sheet,
hardest reported first: **net_cash** (`cashneq + investmentsc − TOTAL debt` — nets
against the full debt line, the XRN discipline) → **ncav** (Graham net-net) →
**tangible_book** (`equity − intangibles`, strips goodwill — the MNRO discipline),
each mapped to the gate's `floor_basis` (net_cash/ncav→`net_net`,
tangible_book→`book`). Two measurement bugs found and fixed with numbers, not
hunches:
- **FX artifact.** Sharadar SF1 is in the filer's reporting currency but DAILY
  marketcap is USD — GRVY (Korea, KRW) showed a phantom ~100% "discount" (616
  billion KRW of book vs a $456M USD cap). Fixed: screen USD reporters only
  (TICKERS `currency`), and because a ticker can carry BOTH a KRW and a USD row,
  any non-USD row forces the ticker out (ambiguous currency ⇒ not screenable).
  Dropped the FX false positives (452 → 354).
- **Financials in disguise.** Mortgage REITs sit under the Real Estate *sector*
  but their "book" is a leveraged marked-to-model mortgage-loan float — a mREIT
  at 0.6x book is the norm, not a floor. Excluded at the *industry* gate
  (`REIT - Mortgage`); equity REITs (own real buildings) are KEPT (354 → 323).
Cash-runway is computed from quarterly `ncfo` and short-runway names are FLAGGED
`eroding_floor` (the ARVN caveat: a burning net-cash floor has a fuse), not
dropped — the dossier stage prices the erosion. Financials (banks/insurers),
warrants/preferred/units/funds, and delisted shells are excluded; small-cap only
($10M–$3B, where neglect lives).

Coverage is deliberately generous (323 below-floor names is a *net*, not a book);
the four-trap verification gate is what turns the net into funded picks. Tests:
`tests/test_neglect_screen.py` (14), `tests/test_hard_catalyst_sourcing.py` (6),
green with the existing forced-seller + verification suites.
