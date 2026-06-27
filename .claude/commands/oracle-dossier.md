# /oracle-dossier — accumulate dossiers only

Pure accumulator — runs without minimum count enforcement and without
triggering scoring or execution. Use this when you want to add a single
new dossier to the corpus.

## Model routing

Same convention as `/oracle-research`: dispatch filing reads to Sonnet via
Agent, reserve the main-session model for synthesis. Filing-reading is
~5× cheaper on Sonnet at near-identical quality.

## Steps

1. Load existing dossiers.
2. Build one new dossier (or as many as requested) via `oracle.research.make_dossier`.
3. Append to the cache. If a dossier for that symbol already exists, REPLACE it (one dossier per symbol).
4. Save via `oracle.research.save_dossiers`.
5. Persist.

NO scoring. NO orders. NO journal entries.
