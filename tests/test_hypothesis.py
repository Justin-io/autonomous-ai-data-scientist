"""Unit tests for Hypothesis Engine."""

import pytest
from core.hypothesis.engine import HypothesisEngine, HypothesisStatus


def test_hypothesis_generation_for_revenue():
    """Verify hypothesis engine generates multiple competing hypotheses for revenue decline."""
    engine = HypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(metric="revenue", direction="decline")

    assert len(hypotheses) >= 4
    categories = [h.category for h in hypotheses]
    assert "VOLUME" in categories
    assert "PRICE_AOV" in categories
    assert "SEGMENT_CHURN" in categories
    assert "REFUND_SURGE" in categories


def test_hypothesis_ranking_by_information_gain():
    """Verify ranking orders hypotheses by expected information gain."""
    engine = HypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(metric="revenue", direction="decline")
    ranked = engine.rank_hypotheses(hypotheses)

    assert ranked[0].information_gain >= ranked[-1].information_gain


def test_bayesian_probability_updating_and_falsification():
    """Verify Bayesian posterior update increases probability on supporting evidence and refutes on falsification."""
    engine = HypothesisEngine()
    hypotheses = engine.generate_competing_hypotheses(metric="revenue", direction="decline")
    h_segment = next(h for h in hypotheses if h.category == "SEGMENT_CHURN")
    h_volume = next(h for h in hypotheses if h.category == "VOLUME")

    # Supporting evidence for segment churn
    updated_seg = engine.update_hypothesis(
        hypothesis=h_segment,
        test_name="Segment Shift-Share Analysis",
        evidence_summary="Enterprise tier revenue dropped by 22% explaining 75% of overall drop",
        supports_hypothesis=True,
        bayes_factor=4.0,
    )
    assert updated_seg.current_probability > updated_seg.prior_probability
    assert updated_seg.status in [HypothesisStatus.TESTING, HypothesisStatus.CONFIRMED]

    # Refuting evidence for overall volume drop
    updated_vol = engine.update_hypothesis(
        hypothesis=h_volume,
        test_name="Total Order Count Comparison",
        evidence_summary="Total order volume was flat (-0.5%), insufficient to explain 8% drop",
        supports_hypothesis=False,
        bayes_factor=4.0,
        falsification_reason="Order volume only dropped 0.5%, ruling out volume as primary driver.",
    )
    assert updated_vol.current_probability < updated_vol.prior_probability
    assert updated_vol.status == HypothesisStatus.REFUTED
    assert updated_vol.falsification_reason is not None

    rejections = engine.get_rejection_summary([updated_seg, updated_vol])
    assert len(rejections) == 1
    assert rejections[0]["id"] == updated_vol.id
