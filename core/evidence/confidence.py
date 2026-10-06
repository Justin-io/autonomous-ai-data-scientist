"""Calibrated Multi-Factor Confidence Scorer."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ConfidenceFactors(BaseModel):
    """Decomposition of calibrated confidence score factors."""

    data_quality: float  # 0.0 to 1.0 (missingness, schema compliance)
    sample_size: float  # 0.0 to 1.0 (statistical power)
    statistical_strength: float  # 0.0 to 1.0 (p-value, effect size)
    semantic_grounding: float  # 0.0 to 1.0 (alignment with semantic layer)
    evidence_completeness: float  # 0.0 to 1.0 (proportion of numbers cited)


class CalibratedConfidenceResult(BaseModel):
    """Calibrated confidence evaluation with factor breakdown."""

    overall_confidence: float  # 0.0 to 1.0
    factors: ConfidenceFactors
    calibration_tier: str  # HIGH, MODERATE, LOW
    triggers_hitl: bool  # True if overall_confidence < 0.70
    decomposition_summary: str


class ConfidenceScorer:
    """Computes calibrated confidence score based on objective analytical factors."""

    def calculate_confidence(
        self,
        data_quality: float = 0.95,
        sample_size: int = 1000,
        p_value: float = 0.001,
        effect_size_magnitude: str = "medium",
        is_semantically_grounded: bool = True,
        cited_ratio: float = 1.0,
        hitl_threshold: float = 0.70,
    ) -> CalibratedConfidenceResult:
        # 1. Sample size factor: saturates around 2,000 observations
        f_sample = min(1.0, max(0.2, sample_size / 1500.0))

        # 2. Data quality factor: clamped
        f_dq = min(1.0, max(0.0, data_quality))

        # 3. Statistical strength factor
        if p_value < 0.001:
            base_stat = 0.95
        elif p_value < 0.01:
            base_stat = 0.85
        elif p_value < 0.05:
            base_stat = 0.75
        else:
            base_stat = 0.40

        eff_bonus = {"large": 0.05, "medium": 0.0, "small": -0.10, "negligible": -0.20}.get(effect_size_magnitude, 0.0)
        f_stat = min(1.0, max(0.1, base_stat + eff_bonus))

        # 4. Semantic grounding
        f_sem = 1.0 if is_semantically_grounded else 0.50

        # 5. Evidence completeness
        f_ev = min(1.0, max(0.0, cited_ratio))

        # Weighted combination:
        # C = 0.20*DQ + 0.20*Sample + 0.25*Stat + 0.15*Semantic + 0.20*Evidence
        score = (
            0.20 * f_dq
            + 0.20 * f_sample
            + 0.25 * f_stat
            + 0.15 * f_sem
            + 0.20 * f_ev
        )
        score = round(min(1.0, max(0.0, score)), 3)

        tier = "HIGH" if score >= 0.85 else ("MODERATE" if score >= 0.70 else "LOW")
        triggers_hitl = (score < hitl_threshold)

        summary = (
            f"Calibrated Confidence: {score:.1%} [{tier} tier]. "
            f"Decomposition: Data Quality {f_dq:.0%}, Sample Size {f_sample:.0%}, "
            f"Statistical Rigor {f_stat:.0%}, Semantic Grounding {f_sem:.0%}, "
            f"Evidence Coverage {f_ev:.0%}."
        )

        return CalibratedConfidenceResult(
            overall_confidence=score,
            factors=ConfidenceFactors(
                data_quality=round(f_dq, 3),
                sample_size=round(f_sample, 3),
                statistical_strength=round(f_stat, 3),
                semantic_grounding=round(f_sem, 3),
                evidence_completeness=round(f_ev, 3),
            ),
            calibration_tier=tier,
            triggers_hitl=triggers_hitl,
            decomposition_summary=summary,
        )
