# /oracle-setup — seed Oracle's $1k sleeve idempotently

Initialize Oracle's sleeve at the $1,000 base. Safe to run repeatedly — if
the sleeve file already exists, this command is a no-op.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. Check for `cache/oracle_sleeve.json`. If present and `cash + sum(positions) > 0`, exit.
2. Construct `OracleSleeve(initial_cash=1000.0)` (`oracle.sleeve.CAPITAL_BASE`).
3. Save to `cache/oracle_sleeve.json`.
4. Persist via `pantheon.persist("oracle", ...)`.

The same pattern applies to Delphi and Achilles — but those have their own
setup steps wired into their main commands. This file is Oracle-specific.
