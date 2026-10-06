"""Anomaly Detection Engine with Automatic Method Selection."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest


class AnomalyPoint(BaseModel):
    """An individual detected anomalous observation."""

    index: int
    label: str
    value: float
    expected_value: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    anomaly_score: float
    explanation: str


class AnomalyReport(BaseModel):
    """Summary report of time-series or distributional anomaly detection."""

    method_used: str
    anomalies: List[AnomalyPoint] = Field(default_factory=list)
    anomaly_count: int
    summary: str


class AnomalyDetector:
    """Robust anomaly detection using IQR, Hampel filter, Rolling Z, and Isolation Forest."""

    def detect_anomalies(
        self,
        series: pd.Series,
        labels: Optional[pd.Series] = None,
        method: str = "auto",
        contamination: float = 0.05,
    ) -> AnomalyReport:
        clean = series.dropna().astype(float)
        n = len(clean)

        if n < 4:
            return AnomalyReport(
                method_used="none",
                anomalies=[],
                anomaly_count=0,
                summary="Insufficient data points for reliable anomaly detection.",
            )

        if labels is None:
            labels = pd.Series([str(i) for i in clean.index], index=clean.index)

        # Automatic method selection
        if method == "auto":
            # For small to medium time-series (< 300), Hampel/MAD or IQR is most robust
            if n < 300:
                method = "hampel"
            else:
                method = "isolation_forest"

        anomalies: List[AnomalyPoint] = []

        if method == "hampel":
            # Hampel filter: median and 3 * 1.4826 * MAD
            med = float(clean.median())
            mad = float(np.median(np.abs(clean - med)))
            sigma = 1.4826 * mad
            threshold = 3.0 * max(1e-6, sigma)

            for idx, val in clean.items():
                diff = abs(val - med)
                if diff > threshold:
                    score = diff / threshold
                    sev = "CRITICAL" if score > 2.0 else ("HIGH" if score > 1.5 else "MEDIUM")
                    dir_str = "spike above" if val > med else "drop below"
                    anomalies.append(
                        AnomalyPoint(
                            index=int(clean.index.get_loc(idx)),
                            label=str(labels.loc[idx]),
                            value=round(val, 2),
                            expected_value=round(med, 2),
                            severity=sev,
                            anomaly_score=round(score, 2),
                            explanation=f"Significant {dir_str} median baseline ({val:.2f} vs expected {med:.2f}, {score:.1f}x threshold).",
                        )
                    )

        elif method == "iqr":
            q25, q75 = np.percentile(clean, [25, 75])
            iqr = q75 - q25
            lower_fence = q25 - 1.5 * iqr
            upper_fence = q75 + 1.5 * iqr
            med = float(clean.median())

            for idx, val in clean.items():
                if val < lower_fence or val > upper_fence:
                    dist = (val - upper_fence) if val > upper_fence else (lower_fence - val)
                    score = dist / max(1e-6, iqr)
                    sev = "HIGH" if score > 1.5 else "MEDIUM"
                    dir_str = "upper outlier" if val > upper_fence else "lower outlier"
                    anomalies.append(
                        AnomalyPoint(
                            index=int(clean.index.get_loc(idx)),
                            label=str(labels.loc[idx]),
                            value=round(val, 2),
                            expected_value=round(med, 2),
                            severity=sev,
                            anomaly_score=round(score, 2),
                            explanation=f"Statistical {dir_str} outside Tukey fences [{lower_fence:.2f}, {upper_fence:.2f}].",
                        )
                    )

        elif method == "isolation_forest":
            iso = IsolationForest(contamination=contamination, random_state=42)
            X = clean.values.reshape(-1, 1)
            preds = iso.fit_predict(X)
            scores = -iso.score_samples(X)
            med = float(clean.median())

            for i, (pred, score) in enumerate(zip(preds, scores)):
                if pred == -1:
                    idx = clean.index[i]
                    val = float(clean.iloc[i])
                    sev = "CRITICAL" if score > 0.70 else "HIGH"
                    anomalies.append(
                        AnomalyPoint(
                            index=i,
                            label=str(labels.iloc[i]),
                            value=round(val, 2),
                            expected_value=round(med, 2),
                            severity=sev,
                            anomaly_score=round(float(score), 3),
                            explanation=f"Isolation Forest identified non-linear distributional anomaly (score: {score:.3f}).",
                        )
                    )

        summary = (
            f"Detected {len(anomalies)} anomalies using {method.upper()} method."
            if anomalies
            else f"No significant anomalies detected using {method.upper()} method."
        )

        return AnomalyReport(
            method_used=method,
            anomalies=anomalies,
            anomaly_count=len(anomalies),
            summary=summary,
        )

    def detect_changepoints(self, series: pd.Series, labels: Optional[pd.Series] = None) -> List[Dict[str, Any]]:
        """Detect abrupt structural breaks / change-points in the mean of a sequence."""
        clean = series.dropna().astype(float).values
        n = len(clean)
        if n < 10:
            return []

        if labels is None:
            labels = pd.Series([str(i) for i in range(n)])

        # Max difference in means across candidate split points
        best_diff = 0.0
        best_idx = -1
        overall_std = np.std(clean)

        for i in range(3, n - 3):
            left_mean = np.mean(clean[:i])
            right_mean = np.mean(clean[i:])
            diff = abs(right_mean - left_mean)
            if diff > best_diff:
                best_diff = diff
                best_idx = i

        changepoints = []
        if overall_std > 0 and (best_diff / overall_std) > 1.2 and best_idx > 0:
            left_m = float(np.mean(clean[:best_idx]))
            right_m = float(np.mean(clean[best_idx:]))
            changepoints.append({
                "split_index": best_idx,
                "label": str(labels.iloc[best_idx]),
                "pre_mean": round(left_m, 2),
                "post_mean": round(right_m, 2),
                "delta": round(right_m - left_m, 2),
                "delta_pct": round(((right_m - left_m) / max(1e-6, abs(left_m))) * 100.0, 2),
                "explanation": f"Structural level shift on {labels.iloc[best_idx]}: mean shifted from {left_m:.2f} to {right_m:.2f} ({((right_m-left_m)/left_m)*100:+.1f}%).",
            })

        return changepoints
