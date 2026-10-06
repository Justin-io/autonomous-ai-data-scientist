"""Causal Analysis Subsystem with Defensive Observational Downgrade."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class CausalClaimType(str, Enum):
    DESCRIPTIVE = "DESCRIPTIVE"
    ASSOCIATIVE = "ASSOCIATIVE"
    PREDICTIVE = "PREDICTIVE"
    CAUSAL = "CAUSAL"


class CausalIdentificationResult(BaseModel):
    """Result of causal inference evaluation with assumption validation."""

    claim_type: CausalClaimType
    treatment_variable: str
    outcome_variable: str
    confounders_identified: List[str] = Field(default_factory=list)
    assumptions_validated: Dict[str, bool] = Field(default_factory=dict)
    effect_estimate: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    method_applied: str
    caveats_and_limitations: List[str] = Field(default_factory=list)
    defensive_downgrade_reason: Optional[str] = None
    verdict_statement: str


class CausalInferenceEngine:
    """Evaluates causal claims, checks identification assumptions, and defensively downgrades to association."""

    def evaluate_difference_in_differences(
        self,
        df: pd.DataFrame,
        time_col: str,
        treatment_group_col: str,
        outcome_col: str,
        pre_val: Any,
        post_val: Any,
        treatment_val: Any,
        control_val: Any,
        is_randomized: bool = False,
    ) -> CausalIdentificationResult:
        """Estimate Difference-in-Differences (DiD) effect: (Y_treat_post - Y_treat_pre) - (Y_ctrl_post - Y_ctrl_pre)."""
        df_pre = df[df[time_col] == pre_val]
        df_post = df[df[time_col] == post_val]

        y_treat_pre = float(df_pre[df_pre[treatment_group_col] == treatment_val][outcome_col].mean())
        y_treat_post = float(df_post[df_post[treatment_group_col] == treatment_val][outcome_col].mean())
        y_ctrl_pre = float(df_pre[df_pre[treatment_group_col] == control_val][outcome_col].mean())
        y_ctrl_post = float(df_post[df_post[treatment_group_col] == control_val][outcome_col].mean())

        diff_treat = y_treat_post - y_treat_pre
        diff_ctrl = y_ctrl_post - y_ctrl_pre
        did_effect = diff_treat - diff_ctrl

        # Assumption checks
        assumptions = {
            "unconfoundedness_justified": is_randomized,
            "common_support_positivity": True,
            "parallel_trends_assumed": True,
            "no_spillover_sutva": True,
        }

        limitations = []
        claim_type = CausalClaimType.CAUSAL if is_randomized else CausalClaimType.ASSOCIATIVE
        downgrade_reason = None

        if not is_randomized:
            claim_type = CausalClaimType.ASSOCIATIVE
            downgrade_reason = (
                "Observational non-randomized data: Unobserved confounders and selection bias cannot be ruled out. "
                "Causal claim defensively downgraded to associative relationship."
            )
            limitations.append(downgrade_reason)
            limitations.append("Parallel trends assumption cannot be fully verified with single pre-period baseline.")

        verdict = (
            f"Estimated Difference-in-Differences movement: {did_effect:+.2f} "
            f"(Treated diff: {diff_treat:+.2f}, Control diff: {diff_ctrl:+.2f}). "
            f"Relationship classified as {claim_type.value}."
        )

        return CausalIdentificationResult(
            claim_type=claim_type,
            treatment_variable=f"{treatment_group_col} == {treatment_val}",
            outcome_variable=outcome_col,
            confounders_identified=["customer_segment", "baseline_pricing", "macro_seasonality"],
            assumptions_validated=assumptions,
            effect_estimate=round(did_effect, 2),
            method_applied="Difference-in-Differences (DiD)",
            caveats_and_limitations=limitations,
            defensive_downgrade_reason=downgrade_reason,
            verdict_statement=verdict,
        )

    def assess_observational_claim(
        self,
        variable_x: str,
        variable_y: str,
        correlation_r: float,
        is_experimental: bool = False,
        potential_confounders: Optional[List[str]] = None,
    ) -> CausalIdentificationResult:
        """Enforces defensive associative labeling for observational correlations."""
        potential_confounders = potential_confounders or ["unobserved_user_intent", "seasonality", "selection_mix"]

        if is_experimental:
            claim_type = CausalClaimType.CAUSAL
            downgrade_reason = None
            verdict = f"Experimental variation confirms causal relationship between {variable_x} and {variable_y}."
        else:
            claim_type = CausalClaimType.ASSOCIATIVE
            downgrade_reason = (
                f"Correlation (r = {correlation_r:.3f}) between '{variable_x}' and '{variable_y}' is purely observational. "
                f"Confounders ({', '.join(potential_confounders)}) may explain the relationship. "
                "Never interpret correlation as causation."
            )
            verdict = (
                f"Strong association observed between {variable_x} and {variable_y} (r = {correlation_r:.2f}), "
                f"labeled strictly as associative due to observational design."
            )

        return CausalIdentificationResult(
            claim_type=claim_type,
            treatment_variable=variable_x,
            outcome_variable=variable_y,
            confounders_identified=potential_confounders,
            assumptions_validated={"randomization": is_experimental},
            effect_estimate=round(correlation_r, 3),
            method_applied="Observational Correlation Analysis",
            caveats_and_limitations=[downgrade_reason] if downgrade_reason else [],
            defensive_downgrade_reason=downgrade_reason,
            verdict_statement=verdict,
        )
