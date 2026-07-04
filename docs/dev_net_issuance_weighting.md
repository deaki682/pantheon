# Development memo — net-issuance weighting (NOT validation)

In-sample development on the SPENT 2000-2025 panel to inform the god's
weighting choice. This is NOT a validated result — the holdout was
already used to validate the equal-weight version, so these numbers are
development, and the forward test is the sole arbiter.

## Result

net-issuance-low N50 LARGE, three weightings, net of costs:

| weighting | in-sample 2000-15 | holdout 2016-25 | vs SPY (~14.3%) |
|---|---|---|---|
| equal-weight (validated) | +9.31% | +14.40% | ties |
| cap-weight | +8.83% | +15.53% | **beats +1.2%/yr** |
| sqrt-cap tilt | +8.89% | +14.50% | ~ties |

## Reading (the honest nuance)

Cap-weight beat SPY in the holdout — but was WORSE than equal-weight
in-sample. So cap-weighting does NOT improve the factor; it captured
the 2016-2025 mega-cap tailwind that equal-weight forfeits. That is a
**regime bet on continued mega-cap dominance**, not a durable edge —
and full cap-weight concentrates 50 names into a few giants, poor
diversification for a small book.

## Decision for the god

Keep the **validated equal-weight** version as the god's core (it is
what earned "supported" and what the forward test tracks). A mild
sqrt-cap tilt is a defensible option but barely differs. Full
cap-weight is NOT adopted — it trades the factor's robustness for a
mega-cap regime bet. If the operator wants the mega-cap tailwind
captured, that is a conscious regime view, tracked as its own forward
arm, not folded into the core silently.
