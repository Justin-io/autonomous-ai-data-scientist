"""Autonomous Hypothesis Engine.

Generates competing, falsifiable hypotheses, ranks them by information gain,
updates Bayesian posterior confidences, records falsification reasons,
and prevents premature convergence on superficial explanations.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class HypothesisStatus(str, Enum):
    PENDING = "PENDING"
    TESTING = "TESTING"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Hypothesis(BaseModel):
    """Falsifiable business hypothesis with Bayesian confidence."""

    id: str
    statement: str
    category: str  # VOLUME, PRICE_AOV, SEGMENT_CHURN, REFUND_SURGE, MIX_SHIFT, EXTERNAL
    prior_probability: float = 0.20
    current_probability: float = 0.20
    status: HypothesisStatus = HypothesisStatus.PENDING
    required_evidence: List[str] = Field(default_factory=list)
    information_gain: float = 0.50
    falsification_reason: Optional[str] = None
    tests_conducted: List[Dict[str, Any]] = Field(default_factory=list)


class HypothesisEngine:
    """Manages generation, ranking, Bayesian probability updates, and rejection logs."""

    def generate_competing_hypotheses(
        self,
        metric: str,
        direction: str,  # "decline", "increase", "anomaly"
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Hypothesis]:
        """Synthesize competing, falsifiable hypotheses for the analytical question."""
        context = context or {}
        hypotheses = []

        if metric in ["revenue", "sales", "mrr"]:
            if direction == "decline":
                hypotheses = [
                    Hypothesis(
                        id="H-01",
                        statement="Transaction/Order volume drop: Fewer customer purchases were completed.",
                        category="VOLUME",
                        prior_probability=0.25,
                        current_probability=0.25,
                        required_evidence=["Compare distinct order count between periods", "Check session traffic"],
                        information_gain=0.75,
                    ),
                    Hypothesis(
                        id="H-02",
                        statement="Basket size / Average Order Value contraction: Customers bought fewer items or cheaper products.",
                        category="PRICE_AOV",
                        prior_probability=0.20,
                        current_probability=0.20,
                        required_evidence=["Calculate AOV difference", "Analyze units per transaction"],
                        information_gain=0.70,
                    ),
                    Hypothesis(
                        id="H-03",
                        statement="High-value Customer Segment churn or contraction: A key account segment (e.g. Enterprise) experienced disproportionate revenue decline.",
                        category="SEGMENT_CHURN",
                        prior_probability=0.25,
                        current_probability=0.25,
                        required_evidence=["Multi-dimensional shift-share decomposition by customer tier", "Segment churn rates"],
                        information_gain=0.85,
                    ),
                    Hypothesis(
                        id="H-04",
                        statement="Refund / Chargeback surge: High rate of returned orders or refund processing eroded net revenue.",
                        category="REFUND_SURGE",
                        prior_probability=0.15,
                        current_probability=0.15,
                        required_evidence=["Calculate monthly refund rates", "Analyze refund reasons"],
                        information_gain=0.65,
                    ),
                    Hypothesis(
                        id="H-05",
                        statement="Product mix shift: Demand migrated away from higher-margin or premium product lines toward low-tier items.",
                        category="MIX_SHIFT",
                        prior_probability=0.15,
                        current_probability=0.15,
                        required_evidence=["Product category revenue breakdown", "Product unit share shift"],
                        information_gain=0.60,
                    ),
                ]
        elif metric in ["conversion_rate", "cvr"]:
            hypotheses = [
                Hypothesis(
                    id="H-01",
                    statement="True treatment efficacy: Redesigned checkout genuinely improved user conversion rates.",
                    category="TREATMENT_EFFECT",
                    prior_probability=0.50,
                    current_probability=0.50,
                    required_evidence=["Overall conversion rate difference", "Two-sample proportions test"],
                    information_gain=0.80,
                ),
                Hypothesis(
                    id="H-02",
                    statement="Simpson's Paradox / Subgroup Traffic Skew: Aggregate lift is an artifact of traffic allocation imbalance across devices or channels.",
                    category="CONFOUNDING_BIAS",
                    prior_probability=0.50,
                    current_probability=0.50,
                    required_evidence=["Stratified conversion rate analysis by device", "Traffic proportion test"],
                    information_gain=0.95,
                ),
            ]
        elif metric in ["refund_rate", "churn_rate"]:
            hypotheses = [
                Hypothesis(
                    id="H-01",
                    statement="Product quality / Defective release: A specific product category or version update experienced elevated failure rates.",
                    category="DEFECT",
                    prior_probability=0.40,
                    current_probability=0.40,
                    required_evidence=["Time-series anomaly detection", "Refund reason breakdown by product"],
                    information_gain=0.85,
                ),
                Hypothesis(
                    id="H-02",
                    statement="Seasonal / Macroeconomic fluctuation: Normal cyclical variation in customer returns.",
                    category="SEASONALITY",
                    prior_probability=0.30,
                    current_probability=0.30,
                    required_evidence=["Historical seasonal decomposition", "Year-over-year comparison"],
                    information_gain=0.60,
                ),
                Hypothesis(
                    id="H-03",
                    statement="Billing / Pricing dispute: Customer dissatisfaction with pricing policy or billing changes.",
                    category="PRICING",
                    prior_probability=0.30,
                    current_probability=0.30,
                    required_evidence=["Refund reason codes", "Pricing change correlation"],
                    information_gain=0.70,
                ),
            ]
        else:
            hypotheses = [
                Hypothesis(
                    id="H-01",
                    statement=f"Metric movement in {metric} is driven by top-line volume changes.",
                    category="VOLUME",
                    prior_probability=0.50,
                    current_probability=0.50,
                    required_evidence=["Volume trend analysis"],
                    information_gain=0.50,
                ),
                Hypothesis(
                    id="H-02",
                    statement=f"Metric movement in {metric} is driven by categorical segment shifts.",
                    category="SEGMENT_SHIFT",
                    prior_probability=0.50,
                    current_probability=0.50,
                    required_evidence=["Segment decomposition"],
                    information_gain=0.50,
                ),
            ]

        return hypotheses

    def rank_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Rank hypotheses by expected information gain and current probability."""
        return sorted(
            hypotheses,
            key=lambda h: (h.information_gain * 0.6 + h.current_probability * 0.4),
            reverse=True,
        )

    def update_hypothesis(
        self,
        hypothesis: Hypothesis,
        test_name: str,
        evidence_summary: str,
        supports_hypothesis: bool,
        bayes_factor: float = 3.0,
        falsification_reason: Optional[str] = None,
    ) -> Hypothesis:
        """Update posterior probability using Bayesian updating and record audit trail."""
        prior = hypothesis.current_probability
        
        if supports_hypothesis:
            # P(H|E) = (P(E|H) * P(H)) / P(E)
            # Odds update: posterior_odds = prior_odds * bayes_factor
            prior_odds = prior / max(1e-6, (1.0 - prior))
            post_odds = prior_odds * bayes_factor
            posterior = post_odds / (1.0 + post_odds)
            hypothesis.current_probability = round(min(0.99, max(0.01, posterior)), 3)
            if hypothesis.current_probability > 0.65:
                hypothesis.status = HypothesisStatus.CONFIRMED
            else:
                hypothesis.status = HypothesisStatus.TESTING
        else:
            prior_odds = prior / max(1e-6, (1.0 - prior))
            post_odds = prior_odds / bayes_factor
            posterior = post_odds / (1.0 + post_odds)
            hypothesis.current_probability = round(min(0.99, max(0.01, posterior)), 3)
            if hypothesis.current_probability < 0.15:
                hypothesis.status = HypothesisStatus.REFUTED
                hypothesis.falsification_reason = falsification_reason or evidence_summary
            else:
                hypothesis.status = HypothesisStatus.TESTING

        hypothesis.tests_conducted.append({
            "test_name": test_name,
            "evidence": evidence_summary,
            "supports": supports_hypothesis,
            "prior_prob": prior,
            "posterior_prob": hypothesis.current_probability,
            "falsification_reason": hypothesis.falsification_reason,
        })
        return hypothesis

    def get_rejection_summary(self, hypotheses: List[Hypothesis]) -> List[Dict[str, Any]]:
        """Return explicit audit log of rejected hypotheses and reasons."""
        return [
            {
                "id": h.id,
                "statement": h.statement,
                "status": h.status.value,
                "final_probability": h.current_probability,
                "falsification_reason": h.falsification_reason,
            }
            for h in hypotheses
            if h.status == HypothesisStatus.REFUTED
        ]
