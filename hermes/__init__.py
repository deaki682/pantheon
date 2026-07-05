"""Hermes — the merger-arbitrage LLM A/B engine (return/convexity pivot's first).

God of commerce, negotiation, and crossing boundaries. Trades small-cap CASH
merger targets: long the target below the offer, hold to resolution. Bounded
CONTRACTUAL floor (the deal-break, ~-15%), convex payoff (many small bounded
wins, rare bounded losses, occasional topping-bid tail).

The experiment (docs/hermes_launch_override.md): Arm A = LLM-judged deal-break
reading, LIVE real money; Arm B = mechanical all-deals, paper control.
LLM-lift = A - B measures, in dollars, whether an LLM reads a deal better than
a screen — the gods' unique power, put on real money and measured.
"""
