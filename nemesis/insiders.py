"""Post-spin Form 4 check — what insiders DO vs what the Form 10 promises.

The dossier's incentive_alignment score starts from the information
statement: equity grants, PSU metrics, converted awards. But those are
*promises drafted before the stock traded*. Greenblatt's sharpest tell is
behavioral and only observable after distribution — an officer spending
their own money on open-market purchases (Form 4 code "P") in the first
weeks of trading is the one signal that cannot be engineered by the
parent's compensation consultants. Heavy code-"S" selling into the
forced-seller dump is the mirror-image warning: the people who read the
internal numbers are exiting alongside the index funds.

This module summarizes that behavior for exactly one spinco. It deliberately
does NOT score anything — the summary feeds the dossier's judgment pass,
where the analyst weighs it against the Form 10's paper incentives, and it
is recorded verbatim in the dossier's post_spin_insider_activity field so
the evidence behind an incentive_alignment revision stays auditable.

Wraps the existing Form 4 plumbing (shared.insiders parses, oracle.lenses
fetches) rather than duplicating it — same parser Oracle's screen trusts.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from shared.insiders import InsiderTxn


def summarize_post_spin(
    txns: list[InsiderTxn], *, since: str
) -> dict:
    """Distill Form 4 transactions on/after `since` (the distribution date)
    into the facts the dossier judgment needs. Pure — feed it captured or
    fetched transactions alike.

    Transactions before `since` are dropped, not judged: pre-distribution
    Form 4s describe the *parent's* equity mechanics (award conversions,
    distribution adjustments), not a view on the spinco's price.
    """
    post = [t for t in txns if t.transaction_date >= since]
    buys = [t for t in post if t.is_open_market_buy]
    sells = [t for t in post if t.transaction_code == "S" and t.shares > 0]

    return {
        "since": since,
        "n_txns": len(post),
        "n_open_market_buys": len(buys),
        "n_buyers": len({t.insider_name for t in buys}),
        "bought_dollars": round(sum(t.dollars for t in buys), 2),
        "buyers": sorted({t.insider_name for t in buys}),
        "n_sells": len(sells),
        "n_sellers": len({t.insider_name for t in sells}),
        "sold_dollars": round(sum(t.dollars for t in sells), 2),
    }


def render_summary(summary: dict) -> str:
    """One auditable sentence for the dossier's post_spin_insider_activity
    field. Absence of buys is stated outright — "no purchases" is itself
    evidence, and an empty string would read as "not checked"."""
    since = summary.get("since", "?")
    if summary.get("n_txns", 0) == 0:
        return (
            f"No Form 4 transactions filed since distribution ({since}) "
            f"as of the sweep."
        )
    parts = []
    if summary.get("n_open_market_buys"):
        names = ", ".join(summary.get("buyers", [])) or "unknown"
        parts.append(
            f"{summary['n_buyers']} insider(s) made "
            f"{summary['n_open_market_buys']} open-market purchase(s) "
            f"totaling ${summary['bought_dollars']:,.0f} ({names})"
        )
    else:
        parts.append("no open-market purchases")
    if summary.get("n_sells"):
        parts.append(
            f"{summary['n_sellers']} insider(s) sold "
            f"${summary['sold_dollars']:,.0f} across {summary['n_sells']} "
            f"transaction(s)"
        )
    else:
        parts.append("no sales")
    return f"Form 4 activity since distribution ({since}): " + "; ".join(parts) + "."


def fetch_post_spin_txns(
    symbol: str,
    cik: str,
    distribution_date: str,
    *,
    today: Optional[str] = None,
) -> list[InsiderTxn]:  # pragma: no cover - network
    """Fetch Form 4 transactions for one spinco CIK back to its
    distribution date. Thin wrapper over Oracle's per-symbol fetcher —
    days_back is computed from the distribution date so the sweep always
    reaches day one of trading, however late in the hold it runs."""
    from oracle.lenses import fetch_insider_txns_for_symbol

    today_s = today or datetime.utcnow().strftime("%Y-%m-%d")
    try:
        gap = (
            datetime.strptime(today_s, "%Y-%m-%d")
            - datetime.strptime(distribution_date, "%Y-%m-%d")
        ).days
    except ValueError:
        gap = 200
    return fetch_insider_txns_for_symbol(
        symbol, cik, days_back=max(gap + 7, 30), today=today_s
    )
