"""Descriptive Statistics Computation."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats


class DescriptiveStats(BaseModel):
    """Summary descriptive statistics for a numeric sample."""

    count: int
    missing_count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float
    iqr: float
    skewness: float
    kurtosis: float


def compute_descriptive_stats(series: pd.Series) -> DescriptiveStats:
    """Compute rigorous descriptive statistics on a pandas Series."""
    clean = series.dropna().astype(float)
    missing = int(series.isna().sum())
    n = len(clean)

    if n == 0:
        return DescriptiveStats(
            count=0,
            missing_count=missing,
            mean=0.0,
            median=0.0,
            std=0.0,
            min=0.0,
            max=0.0,
            q25=0.0,
            q75=0.0,
            iqr=0.0,
            skewness=0.0,
            kurtosis=0.0,
        )

    q25, q75 = np.percentile(clean, [25, 75])
    iqr = q75 - q25
    skew = float(stats.skew(clean)) if n > 2 else 0.0
    kurt = float(stats.kurtosis(clean)) if n > 3 else 0.0

    return DescriptiveStats(
        count=n,
        missing_count=missing,
        mean=round(float(clean.mean()), 4),
        median=round(float(clean.median()), 4),
        std=round(float(clean.std()), 4) if n > 1 else 0.0,
        min=round(float(clean.min()), 4),
        max=round(float(clean.max()), 4),
        q25=round(float(q25), 4),
        q75=round(float(q75), 4),
        iqr=round(float(iqr), 4),
        skewness=round(skew, 4),
        kurtosis=round(kurt, 4),
    )
