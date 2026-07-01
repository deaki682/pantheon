"""Weekly Catalyst Engine — a standalone research/screening tool.

DISCONNECTED FROM THE GODS. This package shares no state with oracle/midas/
delphi/achilles: no sleeve, no ledger, no broker orders, no pantheon.persist
to claude/live. It never trades. It enumerates the coming week's forecastable
events, subtracts what the options market has already priced in, and surfaces
the residual for a human to judge.

The one idea: edge = expected_outcome - what_the_market_already_expects.
"""
