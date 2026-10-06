"""Unit tests for Causal Inference and Critic Agent."""

import pytest
import pandas as pd
from core.causal.engine import CausalInferenceEngine, CausalClaimType
from core.critic.agent import CriticAgent, CriticIssueSeverity
from warehouse.generator import create_in_memory_warehouse


@pytest.fixture(scope="module")
def db_con():
    return create_in_memory_warehouse(seed=42)


def test_causal_inference_observational_downgrade():
    """Verify that non-randomized observational analysis is defensively downgraded to ASSOCIATIVE."""
    engine = CausalInferenceEngine()
    df = pd.DataFrame([
        {"quarter": 2, "segment": "Enterprise", "revenue": 1000.0},
        {"quarter": 3, "segment": "Enterprise", "revenue": 780.0},
        {"quarter": 2, "segment": "SMB", "revenue": 500.0},
        {"quarter": 3, "segment": "SMB", "revenue": 490.0},
    ])

    res = engine.evaluate_difference_in_differences(
        df=df,
        time_col="quarter",
        treatment_group_col="segment",
        outcome_col="revenue",
        pre_val=2,
        post_val=3,
        treatment_val="Enterprise",
        control_val="SMB",
        is_randomized=False,
    )

    assert res.claim_type == CausalClaimType.ASSOCIATIVE
    assert res.defensive_downgrade_reason is not None
    assert "Unobserved confounders" in res.defensive_downgrade_reason
    assert res.effect_estimate == pytest.approx(-210.0, rel=0.01)


def test_critic_simpsons_paradox_trap_detection(db_con):
    """Verify CriticAgent detects Simpson's Paradox on BQ-2 experiment data."""
    df = db_con.execute("SELECT * FROM ab_test_checkout").df()

    critic = CriticAgent()
    issue = critic.audit_simpsons_paradox(
        df=df,
        variant_col="variant",
        subgroup_col="device",
        converted_col="converted",
    )

    assert issue is not None
    assert issue.category == "SIMPSONS_PARADOX"
    assert issue.severity == CriticIssueSeverity.BLOCKING_ERROR
    assert "Simpson's Paradox" in issue.title


def test_critic_multiple_testing_correction():
    """Verify Benjamini-Hochberg False Discovery Rate correction flags p-hacking."""
    critic = CriticAgent()
    # 10 tests, where 3 have p < 0.05, but when adjusted only 1 survives
    raw_p = [0.01, 0.03, 0.048, 0.12, 0.25, 0.40, 0.55, 0.65, 0.80, 0.95]
    adj_p, sig_mask, issue = critic.audit_multiple_testing(raw_p, alpha=0.05)

    assert len(adj_p) == 10
    assert issue is not None
    assert issue.category == "MULTIPLE_TESTING"


def test_critic_causal_overreach_detection():
    """Verify CriticAgent detects causal words in observational narrative."""
    critic = CriticAgent()
    engine = CausalInferenceEngine()
    causal_res = engine.assess_observational_claim("price_increase", "revenue_decline", correlation_r=-0.85, is_experimental=False)

    narrative = "Our analysis proves that the price hike caused the decline in Q3 revenue."
    issue = critic.audit_causal_overreach(narrative, causal_res)

    assert issue is not None
    assert issue.category == "CAUSAL_OVERREACH"
    assert issue.severity == CriticIssueSeverity.BLOCKING_ERROR
