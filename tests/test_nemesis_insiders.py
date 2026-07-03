"""Tests for the post-spin Form 4 summarizer.

The summarizer is the evidence layer under incentive_alignment revisions —
it must count buys/sells correctly, drop pre-distribution mechanics, and
render absence-of-buys as a stated fact rather than an empty string.
"""
import pytest

from nemesis.insiders import render_summary, summarize_post_spin
from shared.insiders import InsiderTxn


def _txn(**overrides):
    defaults = dict(
        symbol="OCTV", insider_name="A. Buyer", insider_title="CEO",
        transaction_code="P", transaction_date="2026-06-15",
        shares=1000.0, price=17.0, dollars=17_000.0,
    )
    defaults.update(overrides)
    return InsiderTxn(**defaults)


class TestSummarizePostSpin:
    def test_counts_open_market_buys(self):
        s = summarize_post_spin(
            [_txn(), _txn(insider_name="B. Also", dollars=5_000.0)],
            since="2026-05-29",
        )
        assert s["n_open_market_buys"] == 2
        assert s["n_buyers"] == 2
        assert s["bought_dollars"] == 22_000.0
        assert s["buyers"] == ["A. Buyer", "B. Also"]

    def test_pre_distribution_txns_dropped(self):
        # Award conversions and distribution mechanics file as Form 4s
        # BEFORE the spinco trades — they are not a view on the price.
        s = summarize_post_spin(
            [_txn(transaction_date="2026-05-20")], since="2026-05-29"
        )
        assert s["n_txns"] == 0
        assert s["n_open_market_buys"] == 0

    def test_distribution_day_included(self):
        s = summarize_post_spin(
            [_txn(transaction_date="2026-05-29")], since="2026-05-29"
        )
        assert s["n_txns"] == 1

    def test_sales_counted_separately(self):
        s = summarize_post_spin(
            [_txn(), _txn(transaction_code="S", insider_name="C. Seller",
                          dollars=40_000.0)],
            since="2026-05-29",
        )
        assert s["n_open_market_buys"] == 1
        assert s["n_sells"] == 1
        assert s["n_sellers"] == 1
        assert s["sold_dollars"] == 40_000.0

    def test_non_p_non_s_codes_ignored(self):
        # Code "A" (grant) and "M" (option exercise) are compensation
        # mechanics, not open-market conviction — neither bucket counts them.
        s = summarize_post_spin(
            [_txn(transaction_code="A"), _txn(transaction_code="M")],
            since="2026-05-29",
        )
        assert s["n_txns"] == 2
        assert s["n_open_market_buys"] == 0
        assert s["n_sells"] == 0

    def test_zero_share_or_price_buy_not_open_market(self):
        # is_open_market_buy requires positive shares AND price.
        s = summarize_post_spin(
            [_txn(shares=0.0), _txn(price=0.0)], since="2026-05-29"
        )
        assert s["n_open_market_buys"] == 0

    def test_same_buyer_two_buys_one_name(self):
        s = summarize_post_spin(
            [_txn(), _txn(transaction_date="2026-06-20", dollars=8_000.0)],
            since="2026-05-29",
        )
        assert s["n_open_market_buys"] == 2
        assert s["n_buyers"] == 1

    def test_empty(self):
        s = summarize_post_spin([], since="2026-05-29")
        assert s["n_txns"] == 0
        assert s["buyers"] == []


class TestRenderSummary:
    def test_no_txns_states_absence(self):
        text = render_summary(summarize_post_spin([], since="2026-05-29"))
        assert "No Form 4 transactions" in text
        assert "2026-05-29" in text

    def test_buys_rendered_with_names_and_dollars(self):
        text = render_summary(
            summarize_post_spin([_txn()], since="2026-05-29")
        )
        assert "A. Buyer" in text
        assert "$17,000" in text
        assert "no sales" in text

    def test_no_buys_stated_outright(self):
        text = render_summary(
            summarize_post_spin(
                [_txn(transaction_code="S", dollars=9_000.0)],
                since="2026-05-29",
            )
        )
        assert "no open-market purchases" in text
        assert "$9,000" in text

    def test_meets_dossier_prose_floor(self):
        # The field may be quoted into dossier prose — even the emptiest
        # rendering must be a real sentence, not a stub.
        text = render_summary(summarize_post_spin([], since="2026-05-29"))
        assert len(text) >= 20


class TestRenderReconciliation:
    def test_clean_sweep_states_completeness(self):
        from nemesis.insiders import render_reconciliation
        out = render_reconciliation({"on_record": 22, "parsed": 22, "failures": 0})
        assert "complete: 22/22" in out
        assert "UNRELIABLE" not in out

    def test_partial_sweep_screams(self):
        from nemesis.insiders import render_reconciliation
        out = render_reconciliation({"on_record": 8, "parsed": 6, "failures": 2})
        assert "INCOMPLETE" in out and "UNRELIABLE" in out

    def test_zero_filings_is_complete_not_failed(self):
        from nemesis.insiders import render_reconciliation
        out = render_reconciliation({"on_record": 0, "parsed": 0, "failures": 0})
        assert "complete: 0/0" in out
