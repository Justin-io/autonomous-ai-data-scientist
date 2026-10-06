"""Unit tests for Evidence Store, Calibrated Confidence, and Claim Verifier."""

import pytest
from core.evidence.store import EvidenceStore
from core.evidence.confidence import ConfidenceScorer
from core.evidence.verifier import EvidenceVerifier


def test_evidence_store_registration_and_lookup():
    """Verify evidence items can be stored, queried, and retrieved."""
    store = EvidenceStore()
    item = store.add_evidence(
        claim_key="q3_revenue",
        numeric_value=3736122.0,
        unit="USD",
        query_sql="SELECT SUM(net_amount) FROM order_items",
        query_hash="abc123hash",
        dataset_hash="data456hash",
        metric_definition="SUM(net_amount)",
    )

    assert item.evidence_id.startswith("EVD-")
    found = store.find_matching_evidence(3736122.0)
    assert found is not None
    assert found.evidence_id == item.evidence_id


def test_confidence_scorer_decomposition():
    """Verify calibrated confidence calculation and factor decomposition."""
    scorer = ConfidenceScorer()
    res = scorer.calculate_confidence(
        data_quality=0.98,
        sample_size=2500,
        p_value=0.0001,
        effect_size_magnitude="large",
        is_semantically_grounded=True,
        cited_ratio=1.0,
    )

    assert res.overall_confidence > 0.85
    assert res.calibration_tier == "HIGH"
    assert res.triggers_hitl is False
    assert res.factors.data_quality == 0.98


def test_confidence_scorer_low_confidence_triggers_hitl():
    """Verify low sample size or poor statistical significance trips HITL review."""
    scorer = ConfidenceScorer()
    res = scorer.calculate_confidence(
        data_quality=0.60,
        sample_size=30,
        p_value=0.45,
        effect_size_magnitude="negligible",
        is_semantically_grounded=False,
        cited_ratio=0.5,
    )

    assert res.overall_confidence < 0.70
    assert res.triggers_hitl is True
    assert res.calibration_tier == "LOW"


def test_evidence_verifier_passed_and_hallucination_detection():
    """Verify EvidenceVerifier passes on verified numbers and catches hallucinations."""
    store = EvidenceStore()
    store.add_evidence(
        claim_key="decline_pct",
        numeric_value=-7.5,
        unit="%",
        query_sql="SELECT ...",
        query_hash="q1",
        dataset_hash="d1",
        metric_definition="revenue_growth_rate",
    )
    store.add_evidence(
        claim_key="q3_revenue",
        numeric_value=3736122.0,
        unit="USD",
        query_sql="SELECT ...",
        query_hash="q2",
        dataset_hash="d2",
        metric_definition="total_net_revenue",
    )

    verifier = EvidenceVerifier(store)

    # 1. Fully verified text
    clean_text = "Revenue in Q3 reached $3,736,122, representing a -7.5% decline from Q2."
    rep_pass = verifier.verify_report(clean_text)
    assert rep_pass.passed is True
    assert rep_pass.unsupported_claims_count == 0
    assert rep_pass.unsupported_claim_rate == 0.0

    # 2. Text containing hallucinated numbers (e.g. 45.8% and $99,999,999)
    hallucinated_text = "Revenue dropped by 45.8% while total sales were $99,999,999."
    rep_fail = verifier.verify_report(hallucinated_text)
    assert rep_fail.passed is False
    assert rep_fail.unsupported_claims_count == 2
    assert rep_fail.unsupported_claim_rate > 0.0
