"""Inferential Statistics, Hypothesis Testing, and Effect Sizes."""

from __future__ import annotations

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats


class HypothesisTestResult(BaseModel):
    """Result of an inferential hypothesis test with effect size and confidence interval."""

    test_name: str
    statistic: float
    p_value: float
    is_statistically_significant: bool  # at alpha = 0.05
    alpha: float = 0.05
    effect_size_name: str
    effect_size_value: float
    effect_size_interpretation: str  # small, medium, large, negligible
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    normality_assumed: bool
    conclusion: str


class InferentialStatsEngine:
    """Rigorous statistical testing engine with assumption checking and effect sizes."""

    @staticmethod
    def compare_two_means(
        sample_a: pd.Series,
        sample_b: pd.Series,
        label_a: str = "Control / Q2",
        label_b: str = "Treatment / Q3",
        alpha: float = 0.05,
    ) -> HypothesisTestResult:
        """Compare two continuous samples with automatic normality check, Welch's t-test, Mann-Whitney U, and Cohen's d."""
        a = sample_a.dropna().astype(float).values
        b = sample_b.dropna().astype(float).values

        if len(a) < 2 or len(b) < 2:
            return HypothesisTestResult(
                test_name="Insufficient Data",
                statistic=0.0,
                p_value=1.0,
                is_statistically_significant=False,
                effect_size_name="Cohen's d",
                effect_size_value=0.0,
                effect_size_interpretation="indeterminate",
                ci_lower=0.0,
                ci_upper=0.0,
                normality_assumed=False,
                conclusion="Insufficient sample size to compute hypothesis test.",
            )

        # 1. Normality check (Shapiro-Wilk if n < 5000, else D'Agostino Pearson)
        is_normal = True
        try:
            if len(a) <= 5000:
                p_norm_a = stats.shapiro(a[:5000]).pvalue
            else:
                p_norm_a = stats.normaltest(a).pvalue

            if len(b) <= 5000:
                p_norm_b = stats.shapiro(b[:5000]).pvalue
            else:
                p_norm_b = stats.normaltest(b).pvalue

            is_normal = (p_norm_a > 0.01 and p_norm_b > 0.01)
        except Exception:
            is_normal = False

        # 2. Compute Test Statistic & P-value
        mean_a, mean_b = np.mean(a), np.mean(b)
        std_a, std_b = np.std(a, ddof=1), np.std(b, ddof=1)
        n_a, n_b = len(a), len(b)

        # Welch's t-test (robust against unequal variances)
        t_stat, t_pval = stats.ttest_ind(b, a, equal_var=False)

        # Mann-Whitney U test (non-parametric)
        u_stat, u_pval = stats.mannwhitneyu(b, a, alternative="two-sided")

        # Choose primary test based on normality
        if is_normal:
            test_name = "Welch's Two-Sample t-test"
            stat = float(t_stat)
            pval = float(t_pval)
        else:
            test_name = "Mann-Whitney U Test (Non-Parametric)"
            stat = float(u_stat)
            pval = float(u_pval)

        # 3. Effect Size: Cohen's d with pooled variance
        pooled_std = math.sqrt(((n_a - 1) * (std_a ** 2) + (n_b - 1) * (std_b ** 2)) / max(1, n_a + n_b - 2))
        if pooled_std > 0:
            cohens_d = (mean_b - mean_a) / pooled_std
        else:
            cohens_d = 0.0

        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            interp = "negligible"
        elif abs_d < 0.5:
            interp = "small"
        elif abs_d < 0.8:
            interp = "medium"
        else:
            interp = "large"

        # 4. Confidence Interval for difference in means (mean_b - mean_a)
        diff = mean_b - mean_a
        se_diff = math.sqrt((std_a ** 2 / n_a) + (std_b ** 2 / n_b))
        df_welch = ((std_a**2 / n_a + std_b**2 / n_b)**2) / max(
            1e-9, ((std_a**2 / n_a)**2 / (n_a - 1) + (std_b**2 / n_b)**2 / (n_b - 1))
        )
        t_crit = stats.t.ppf(1 - alpha / 2, df=df_welch)
        ci_lower = diff - t_crit * se_diff
        ci_upper = diff + t_crit * se_diff

        sig = bool(pval < alpha)
        direction = "increase" if diff > 0 else "decrease"
        conclusion = (
            f"Statistically significant {direction} (p = {pval:.4e} < {alpha}) with {interp} effect size "
            f"(Cohen's d = {cohens_d:.3f}). 95% CI of difference: [{ci_lower:.2f}, {ci_upper:.2f}]."
            if sig
            else f"No statistically significant difference detected (p = {pval:.4f} >= {alpha})."
        )

        return HypothesisTestResult(
            test_name=test_name,
            statistic=round(stat, 4),
            p_value=round(pval, 6),
            is_statistically_significant=sig,
            alpha=alpha,
            effect_size_name="Cohen's d",
            effect_size_value=round(cohens_d, 4),
            effect_size_interpretation=interp,
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
            confidence_level=1.0 - alpha,
            normality_assumed=bool(is_normal),
            conclusion=conclusion,
        )

    @staticmethod
    def compare_proportions(
        successes_a: int,
        total_a: int,
        successes_b: int,
        total_b: int,
        label_a: str = "Control",
        label_b: str = "Treatment",
        alpha: float = 0.05,
    ) -> HypothesisTestResult:
        """Compare two binomial proportions (e.g. conversion rates, refund rates) with Chi-Square & Relative Risk."""
        p_a = successes_a / max(1, total_a)
        p_b = successes_b / max(1, total_b)
        
        # 2x2 contingency table: [[success, fail], [success, fail]]
        table = [
            [successes_b, total_b - successes_b],
            [successes_a, total_a - successes_a],
        ]
        chi2, p_val, dof, _ = stats.chi2_contingency(table, correction=True)

        # Effect Size: Relative Risk and Cohen's h
        rr = p_b / max(1e-6, p_a)
        h = 2 * math.asin(math.sqrt(p_b)) - 2 * math.asin(math.sqrt(p_a))
        abs_h = abs(h)
        if abs_h < 0.2:
            interp = "negligible"
        elif abs_h < 0.5:
            interp = "small"
        elif abs_h < 0.8:
            interp = "medium"
        else:
            interp = "large"

        # 95% CI for difference in proportions (p_b - p_a)
        diff = p_b - p_a
        se = math.sqrt((p_a * (1 - p_a) / max(1, total_a)) + (p_b * (1 - p_b) / max(1, total_b)))
        z_crit = 1.96
        ci_lower = diff - z_crit * se
        ci_upper = diff + z_crit * se

        sig = bool(p_val < alpha)
        direction = "lift" if diff > 0 else "decline"
        conclusion = (
            f"Statistically significant {direction} in proportion ({p_b*100:.2f}% vs {p_a*100:.2f}%, "
            f"Chi2 = {chi2:.2f}, p = {p_val:.4e}) with Relative Risk = {rr:.3f}. 95% CI of diff: [{ci_lower*100:.2f}%, {ci_upper*100:.2f}%]."
            if sig
            else f"No statistically significant difference in proportions (p = {p_val:.4f} >= {alpha})."
        )

        return HypothesisTestResult(
            test_name="Pearson's Chi-Square Test with Continuity Correction",
            statistic=round(float(chi2), 4),
            p_value=round(float(p_val), 6),
            is_statistically_significant=sig,
            alpha=alpha,
            effect_size_name="Relative Risk",
            effect_size_value=round(rr, 4),
            effect_size_interpretation=interp,
            ci_lower=round(ci_lower, 4),
            ci_upper=round(ci_upper, 4),
            confidence_level=1.0 - alpha,
            normality_assumed=True,
            conclusion=conclusion,
        )
