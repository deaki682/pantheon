# Pantheon research ledger

One row per completed study: what was asked, what the data said, what
changed because of it. Every study has a pre-registration committed
BEFORE its data existed and a results doc with the raw event table.
Newest first. This file is the index — update it the same commit as
any new results doc.

| Date | Study | Verdict | What changed | Docs |
|---|---|---|---|---|
| 2026-07-04 | Proteus lab: IPO lockup-expiration reversion (small-cap) | **REFUTED**: mean excess −10.4% (shrunk −8.0%), t −0.62, median −33%, win rate 28% across n=65 complete 2023 small-cap IPO population (15/80 unpriceable due to broker delisting-data gaps, all 5 spot-checked were distress outcomes — true effect likely worse). Sign of the naive mean is itself an artifact of one +1011% outlier. | First strategy in Proteus's lab (`hypotheses_ever`=1). `ipo_lockup_reversion` terminal-refuted; no forward test (backtest must be `supported` to earn one). Small-cap IPOs keep falling past the lockup date rather than reverting — looks like ordinary small-cap-IPO underperformance continuing, not a distinct reversal. | [prereg](proteus_lab_prereg_ipo_lockup_reversion.md) · [results](proteus_lab_results_ipo_lockup_reversion.md) |
| 2026-07-04 | Guidance exhibit rerun + Midas veto probe | Guidance: exhibit fix lifts hit rate 0%→1.1%; raised n=9 graded (+2.5%, t 0.4) — **INCONCLUSIVE by construction**; channel structurally too thin to validate (classifier also blind to "outlook" phrasing). Veto probe: **0/50 flips** — Midas's disqualification gate measured rock-stable. | No rule changes. Design principle recorded: enumerated binary gates are stable; threshold-adjacent continuous scores are dice. | addenda in [guidance results](midas_guidance_results_2026-07.md) + [consistency results](pantheon_decision_consistency_results_2026-07.md) |
| 2026-07-04 | Midas convergence correction + FLATTEN (operator directive) | Double-count bug fixed (134/934 events had same-day earnings+guidance filings; 104 reclassified; 7/10 of this week's live finalists incl. DAKT were tier-inflated). Corrected re-test: **still REFUTED** (spread −0.87%). | **Live formula flattened**: score = max timing-weighted strength; multiplier survives only as `score_legacy`, ghost-traded weekly (live_pick vs legacy_pick A/B in /midas-ghost). Reversal requires its own prereg at ≥20 graded weeks. | [correction](midas_convergence_correction_results_2026-07.md) · rule-change record in midas.md |
| 2026-07-04 | LLM integration audit (all 5 gods) | **17/23 findings CONFIRMED** (adversarially verified). All 5 HIGH severity fixed same day with operator sign-off. | /oracle-score disabled; Midas runbook contradiction + fail-open freshness gate fixed; Oracle prose gate added (mirrors Nemesis); Delphi decision-log stub gate added. 348 tests green. 12 MEDIUM/LOW findings remain open. | [results](pantheon_llm_integration_audit_2026-07.md) |
| 2026-07-04 | Decision-consistency sweep (Oracle + Midas) | **Oracle TRIGGERED** (40% cohort selection-flip on blind re-score — conviction is load-bearing, genuine instability). **Midas measured but N/A**: expected_value 80% unstable, but that field is informational-only in the code (pick_winner uses a mechanical score) — near-miss caught before wiring a pointless rule; disqualify-veto consistency remains untested. | 3-draw median conviction MANDATORY for boundary cohort names (oracle.md). No Midas rule change; real follow-up is veto-consistency. | [prereg](pantheon_prereg_decision_consistency.md) · [results](pantheon_decision_consistency_results_2026-07.md) |
| 2026-07-04 | Blinded reader accuracy | **BLOCKED — infeasible**: de-anon gate identified 48/48 masked spinoffs (famous names are un-blindable by business description). Clean n=0. | Deep reads CANCELLED. Reframes the ≥20-grade live ghost race as THE reader-accuracy test (prospective, only uncontaminated venue). | [prereg](nemesis_prereg_blinded_reader.md) · [results](nemesis_blinded_reader_results_2026-07.md) |
| 2026-07-04 | Midas guidance channel | **INCONCLUSIVE**: 0 raised in 900 (classifier reads 7.01/8.01 cover shells, not the exhibit press release — verified). | Flag: audit whether LIVE guidance path reads exhibits; if not, channel is near-inert in production. No rule changed. | [prereg](midas_prereg_guidance_channel.md) · [results](midas_guidance_results_2026-07.md) |
| 2026-07-04 | Midas convergence test | **REFUTED**: quiet clusters +1.13% at 5d; 2+ co-signals −0.14%, monotonically wrong direction (892 events, complete catalogs). | Pick memo may not cite convergence count as conviction (midas.md); multipliers run as coded pending live grades. | [prereg](midas_prereg_convergence_test.md) · [results](midas_convergence_results_2026-07.md) |
| 2026-07-03 | Pantheon correlated drawdown | **No new breaker** — book-level −25% halt fails false-trigger budget (47% vs 5%); per-god halts pass worst measured episode. GFC-scale loses ~half regardless: a capital-allocation fact, not a rule gap. | Nothing (per frozen criterion — that IS the result). Betas for all five gods now measured. | [prereg](pantheon_prereg_correlated_drawdown.md) · [results](pantheon_drawdown_results_2026-07.md) |
| 2026-07-03 | Nemesis exit curves (LOOK DON'T TOUCH) | Excess rises monotonically past the 150d hold (+20.5% at 270d, t 1.6, in-sample). Re-rating may take 7–9 months. | Nothing — frozen rules stand; longer hold needs fresh-data prereg. | [results](nemesis_exit_curves_2026-07.md) |
| 2026-07-03 | Spinoff ocean extension 2021–24 | **Trigger is regime-dependent**: −1.0% mean excess per event (t −0.2) across 48 bear/normal-vintage events; the warm-vintage +41% does not generalize. | Runbook risk disclosure (nemesis.md); expectations recalibrated. Veto remains the measured value. | [prereg](nemesis_prereg_ocean_extension.md) · [results](nemesis_ocean_extension_results_2026-07.md) |
| 2026-07-03 | Judge-consistency probe | **Triggered**: FDXF's pass-line call flipped 4/5 on identical extractions; RNA stable 0/5. Boundary judgments are dice. | **3-judge median now MANDATORY** for boundary names (nemesis.md stage 5). FDXF Aug re-read runs under it. | [prereg](nemesis_prereg_judge_consistency.md) · [results](nemesis_judge_consistency_results_2026-07.md) |
| 2026-07-03 | Oracle cluster replay (full population) | **REFUTED as auto-buy**: −6.4%/yr vs IWM at 12mo (n=291, win 32%); convergence not validated (quality lens the drag, 13D the only positive); 5–10d cut mildly positive. | Base-rate priors into oracle-research.md (reading calibration only). Quality-lens fix queued for fresh-data prereg before cohort-2. 253-name live tail → dossier candidates. | [prereg](oracle_prereg_cluster_replay.md) · [results](oracle_replay_results_2026-07.md) |
| 2026-07-03 | Achilles reaction gate | **Inconclusive, buy-side absent**: rewarded reports show no 5-day drift anywhere (small/mid −0.9%); sold reports keep falling (−1.6%, t −2.3) — the ban half is real. | Nothing mechanical (prereg committed either way). Fall season = live test of beats+confirmations. | [prereg](achilles_prereg_reaction_gate.md) · [results](achilles_replay_results_2026-07.md) |
| 2026-07-03 | Nemesis 2025–26 ocean + veto scorecard | Buy-all +41.2% vs SPY +30.2% (trailed IWM +45%); veto 3/3 pre-registered criteria, condemned the worst name (TWNPQ −58%). | v2 veto entry rule live (operator directive); three-leg ghost race running to ≥20-grade checkpoint. | runbook + `cache/ghost_nemesis_deepread_audit.json` |
| (earlier) | Nemesis news-bounce prereg | FAILED — reported anyway; the precedent for one-shot honesty. | Nothing. | [prereg](nemesis_prereg_news_bounce.md) |

## Standing findings (the pattern across studies)

1. Every mechanical BUY trigger tested to date measures ≈ zero-to-
   negative on its own. Every AVOIDANCE rule tested measures real:
   sold-report ban, spinoff veto, boundary-panel rule.
2. All ponds are lottery-shaped: win rates 32–50%, fat right tails.
   Selection layers carry the entire burden of proof — that is what
   the live graded calls and capital gates exist to test.
3. All five gods are high-beta long equity (β 1.0–1.4, measured).
   The correlated month is expected weather; the capital dial is the
   only tail lever.

## Rules of this ledger

- Prereg before data; one dataset buys one decision, once.
- LOOK-DON'T-TOUCH outputs may not be cited for rule changes without
  a fresh-data prereg.
- Failed and inconclusive studies get rows with the same prominence
  as wins.
- Since 2026-07-04 the house lab (`shared.lab`, `/lab`, backlog at
  docs/RESEARCH_BACKLOG.md) runs tradable hypotheses through one
  registry (`cache/lab_registry.json`) with ONE house-wide
  `hypotheses_ever` multiple-testing counter — per-god counters are
  forbidden because sharding the denominator flatters everyone.
  Lab verdicts still land here as rows, same rules as any study.
