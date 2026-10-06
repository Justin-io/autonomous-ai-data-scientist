"""Benchmark Question Suite for Autonomous AI Data Scientist Platform."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    """Specification of an evaluation benchmark scenario."""

    id: str
    question: str
    target_metric: str
    scenario_type: str  # REVENUE_DECLINE, SIMPSONS_PARADOX, ANOMALY_SURGE
    expected_primary_driver: str
    known_trap: Optional[str] = None
    expected_findings: List[str] = Field(default_factory=list)


def get_default_benchmarks() -> List[BenchmarkCase]:
    """Return canonical benchmark suite."""
    return [
        BenchmarkCase(
            id="BQ-1",
            question="Why did our revenue decline 8% this quarter?",
            target_metric="revenue",
            scenario_type="REVENUE_DECLINE",
            expected_primary_driver="Enterprise",
            known_trap="Confounding seasonal dip vs Enterprise price adjustment attrition",
            expected_findings=[
                "Net revenue dropped by approximately 7.5% to 8.5%",
                "Enterprise segment accounts for >70% of total delta",
                "Changepoint detected on July 1st coinciding with pricing change",
                "Causal claim defensively labeled associative due to observational design",
            ],
        ),
        BenchmarkCase(
            id="BQ-2",
            question="Did our new checkout redesign increase overall conversion rate, and should we roll it out to all users?",
            target_metric="conversion_rate",
            scenario_type="SIMPSONS_PARADOX",
            expected_primary_driver="Device Traffic Allocation Confounder",
            known_trap="Simpson's Paradox: Aggregate conversion shows lift (+36.6% vs 26.8%), but desktop and mobile subgroup conversion both drop",
            expected_findings=[
                "Critic Agent detects Simpson's Paradox",
                "Stratified subgroup analysis reveals Control A is superior across both desktop and mobile",
                "Rollout recommendation is firmly REJECTED or paused",
            ],
        ),
        BenchmarkCase(
            id="BQ-3",
            question="What caused the sharp increase in customer churn and refund requests in August 2024?",
            target_metric="refund_rate",
            scenario_type="ANOMALY_SURGE",
            expected_primary_driver="Defective Pro Tools Update",
            known_trap="Mistaking August software defect spike for regular summer seasonality",
            expected_findings=[
                "Anomaly detection isolates August 1st-7th refund surge (>13% vs 2% baseline)",
                "Product line segmentation identifies Pro Tools defect as primary cause",
                "Accelerated churn in Pro tier followed the refund surge",
            ],
        ),
    ]
