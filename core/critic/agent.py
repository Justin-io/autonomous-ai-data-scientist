"""Independent Critic Agent.

Audits analytical trajectories for Simpson's Paradox, Multiple Testing / P-hacking,
Denominator errors, Survivorship bias, and Unsupported Causal Claims.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from core.orchestrator.context import AnalysisState, AnalysisContext
from core.causal.engine import CausalClaimType, CausalIdentificationResult


class CriticIssueSeverity(str, Enum):
    BLOCKING_ERROR = "BLOCKING_ERROR"
    WARNING = "WARNING"
    ADVISORY = "ADVISORY"


class CriticAuditItem(BaseModel):
    """An analytical trap or vulnerability detected by the Critic Agent."""

    category: str  # SIMPSONS_PARADOX, MULTIPLE_TESTING, CAUSAL_OVERREACH, DENOMINATOR_ERROR, PII_LEAK
    severity: CriticIssueSeverity
    title: str
    description: str
    recommended_action: str
    target_rework_state: Optional[AnalysisState] = None


class CriticReport(BaseModel):
    """Comprehensive critique report evaluating analysis trajectory."""

    passed: bool
    issues: List[CriticAuditItem] = Field(default_factory=list)
    overall_risk_score: float = 0.0  # 0.0 (safe) to 1.0 (dangerous)
    rework_required: bool = False
    target_rework_state: Optional[AnalysisState] = None
    audit_summary: str


class CriticAgent:
    """Independent auditor searching for cognitive and statistical traps in analysis."""

    def audit_simpsons_paradox(
        self,
        df: pd.DataFrame,
        variant_col: str,
        subgroup_col: str,
        converted_col: str,
        control_val: str = "control_A",
        treatment_val: str = "treatment_B",
    ) -> Optional[CriticAuditItem]:
        """Detect Simpson's paradox where aggregate direction contradicts all subgroup directions."""
        # 1. Aggregate rate
        ctrl_agg = df[df[variant_col] == control_val][converted_col].mean()
        treat_agg = df[df[variant_col] == treatment_val][converted_col].mean()
        agg_diff = treat_agg - ctrl_agg

        # 2. Subgroup rates
        subgroups = df[subgroup_col].unique()
        sub_diffs = {}
        for sub in subgroups:
            sub_df = df[df[subgroup_col] == sub]
            c_rate = sub_df[sub_df[variant_col] == control_val][converted_col].mean()
            t_rate = sub_df[sub_df[variant_col] == treatment_val][converted_col].mean()
            sub_diffs[sub] = t_rate - c_rate

        # Check for paradox: Aggregate positive lift, but ALL subgroups have negative lift
        if agg_diff > 0 and all(d < 0 for d in sub_diffs.values()):
            return CriticAuditItem(
                category="SIMPSONS_PARADOX",
                severity=CriticIssueSeverity.BLOCKING_ERROR,
                title="Critical Trap: Simpson's Paradox Detected",
                description=(
                    f"Aggregate conversion suggests Treatment B wins (+{agg_diff*100:.2f}%), but within EVERY subgroup "
                    f"({', '.join(f'{k}: {v*100:+.2f}%' for k, v in sub_diffs.items())}), Control A is strictly superior! "
                    "The aggregate lift is entirely driven by confounding subgroup traffic allocation imbalance."
                ),
                recommended_action="Do not roll out treatment. Stratify by device/segment and report subgroup rates.",
                target_rework_state=AnalysisState.SEGMENTS_ANALYZED,
            )

        # Reverse paradox: Aggregate negative, all subgroups positive
        if agg_diff < 0 and all(d > 0 for d in sub_diffs.values()):
            return CriticAuditItem(
                category="SIMPSONS_PARADOX",
                severity=CriticIssueSeverity.BLOCKING_ERROR,
                title="Critical Trap: Simpson's Paradox Detected (Reverse)",
                description="Aggregate performance is negative despite all subgroups showing positive lift.",
                recommended_action="Stratify by confounder variable.",
                target_rework_state=AnalysisState.SEGMENTS_ANALYZED,
            )

        return None

    def audit_multiple_testing(
        self,
        p_values: List[float],
        alpha: float = 0.05,
    ) -> Tuple[List[float], List[bool], Optional[CriticAuditItem]]:
        """Apply Benjamini-Hochberg False Discovery Rate (FDR) multiple testing correction."""
        m = len(p_values)
        if m <= 1:
            return p_values, [p < alpha for p in p_values], None

        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]

        # BH critical thresholds: (k / m) * alpha
        adjusted_p = np.zeros(m)
        is_sig = np.zeros(m, dtype=bool)

        for i, idx in enumerate(sorted_indices):
            rank = i + 1
            threshold = (rank / m) * alpha
            adj_p = min(1.0, sorted_p[i] * (m / rank))
            adjusted_p[idx] = adj_p
            is_sig[idx] = sorted_p[i] <= threshold

        raw_sig_count = sum(p < alpha for p in p_values)
        corrected_sig_count = int(np.sum(is_sig))

        issue = None
        if raw_sig_count > corrected_sig_count:
            issue = CriticAuditItem(
                category="MULTIPLE_TESTING",
                severity=CriticIssueSeverity.WARNING,
                title="P-Hacking / Multiple Testing Inflation Detected",
                description=(
                    f"{raw_sig_count} tests appeared significant at raw alpha={alpha}, but only "
                    f"{corrected_sig_count} survive Benjamini-Hochberg False Discovery Rate correction across {m} tests."
                ),
                recommended_action="Report FDR-adjusted p-values to prevent spurious conclusions.",
                target_rework_state=None,
            )

        return list(adjusted_p), list(is_sig), issue

    def audit_causal_overreach(
        self,
        narrative_text: str,
        causal_result: Optional[CausalIdentificationResult] = None,
    ) -> Optional[CriticAuditItem]:
        """Detect unwarranted causal claims in natural language when analysis is observational."""
        if not causal_result or causal_result.claim_type == CausalClaimType.CAUSAL:
            return None

        causal_words = ["caused by", "causes", "caused the", "proves that", "directly resulted from", "led to the decline"]
        text_lower = narrative_text.lower()
        found = [w for w in causal_words if w in text_lower]

        if found:
            return CriticAuditItem(
                category="CAUSAL_OVERREACH",
                severity=CriticIssueSeverity.BLOCKING_ERROR,
                title="Unsupported Causal Claim Detected",
                description=(
                    f"Narrative asserts causal language ({found}) on observational data where identification "
                    f"was downgraded to {causal_result.claim_type.value}. Reason: {causal_result.defensive_downgrade_reason}"
                ),
                recommended_action="Rephrase language to associative/correlational terms (e.g. 'is associated with', 'coincided with').",
                target_rework_state=AnalysisState.REPORT_DRAFTED,
            )
        return None

    def review_trajectory(self, context: AnalysisContext) -> CriticReport:
        """Run all audit checks across the full analysis context."""
        issues: List[CriticAuditItem] = []
        rework = False
        target_rework = None

        # 1. Simpson's paradox check if checkout test is present
        if "ab_test_checkout" in context.query_results:
            df = pd.DataFrame(context.query_results["ab_test_checkout"])
            sp_issue = self.audit_simpsons_paradox(
                df=df,
                variant_col="variant",
                subgroup_col="device",
                converted_col="converted",
            )
            if sp_issue:
                issues.append(sp_issue)
                if sp_issue.severity == CriticIssueSeverity.BLOCKING_ERROR:
                    rework = True
                    target_rework = sp_issue.target_rework_state

        # 2. Causal overreach check if report is drafted
        if context.final_report and context.causal_inference:
            causal_res = CausalIdentificationResult(**context.causal_inference)
            causal_issue = self.audit_causal_overreach(context.final_report, causal_res)
            if causal_issue:
                issues.append(causal_issue)
                if causal_issue.severity == CriticIssueSeverity.BLOCKING_ERROR:
                    rework = True
                    target_rework = causal_issue.target_rework_state

        # Calculate risk score
        risk = sum(1.0 if i.severity == CriticIssueSeverity.BLOCKING_ERROR else 0.4 for i in issues)
        risk = min(1.0, risk)
        passed = (len([i for i in issues if i.severity == CriticIssueSeverity.BLOCKING_ERROR]) == 0)

        summary = (
            f"Critique PASSED with {len(issues)} advisory warnings."
            if passed
            else f"Critique REJECTED with {len(issues)} blocking issues. Rework required at {target_rework.value if target_rework else 'earlier state'}."
        )

        return CriticReport(
            passed=passed,
            issues=issues,
            overall_risk_score=round(risk, 2),
            rework_required=rework,
            target_rework_state=target_rework,
            audit_summary=summary,
        )
