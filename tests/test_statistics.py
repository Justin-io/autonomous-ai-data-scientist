"""Unit tests for Descriptive, Inferential, Anomaly, and Segmentation engines."""

import pytest
import numpy as np
import pandas as pd
from core.statistics.descriptive import compute_descriptive_stats
from core.statistics.inferential import InferentialStatsEngine
from core.statistics.anomalies import AnomalyDetector
from core.statistics.segmentation import SegmentationEngine
from warehouse.generator import create_in_memory_warehouse


@pytest.fixture(scope="module")
def db_con():
    return create_in_memory_warehouse(seed=42)


def test_compute_descriptive_stats():
    """Verify descriptive statistics computation."""
    data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 100.0])
    stats = compute_descriptive_stats(data)

    assert stats.count == 6
    assert stats.mean == 41.6667
    assert stats.median == 35.0
    assert stats.min == 10.0
    assert stats.max == 100.0
    assert stats.iqr > 0


def test_inferential_compare_two_means():
    """Verify Welch's t-test / Mann-Whitney U on simulated treatment effect."""
    rng = np.random.default_rng(42)
    control = pd.Series(rng.normal(100, 15, size=200))
    treatment = pd.Series(rng.normal(115, 15, size=200))

    res = InferentialStatsEngine.compare_two_means(control, treatment)
    assert res.is_statistically_significant is True
    assert res.p_value < 0.001
    assert res.effect_size_name == "Cohen's d"
    assert res.effect_size_value > 0.8  # Large effect
    assert res.ci_lower > 0  # Confirms treatment > control


def test_inferential_compare_proportions():
    """Verify Chi-Square and Relative Risk on conversion proportion."""
    # Control: 200 / 1000 = 20%
    # Treatment: 280 / 1000 = 28%
    res = InferentialStatsEngine.compare_proportions(
        successes_a=200, total_a=1000, successes_b=280, total_b=1000
    )
    assert res.is_statistically_significant is True
    assert res.p_value < 0.001
    assert res.effect_size_value == pytest.approx(1.4, rel=0.05)


def test_anomaly_detection_hampel_and_iqr():
    """Verify anomaly detection catches injected spike."""
    values = [50.0] * 30
    values[15] = 250.0  # Massive spike
    series = pd.Series(values)

    detector = AnomalyDetector()
    report = detector.detect_anomalies(series, method="hampel")
    assert report.anomaly_count >= 1
    assert any(a.index == 15 for a in report.anomalies)
    assert report.anomalies[0].severity in ["HIGH", "CRITICAL"]


def test_changepoint_detection():
    """Verify change-point detection detects level shift."""
    series = pd.Series([100.0] * 20 + [75.0] * 20)
    detector = AnomalyDetector()
    cps = detector.detect_changepoints(series)

    assert len(cps) >= 1
    assert 18 <= cps[0]["split_index"] <= 22
    assert cps[0]["delta"] < 0


def test_segmentation_shift_share_decomposition(db_con):
    """Verify shift-share contribution analysis isolates Enterprise segment in Q2 vs Q3 data."""
    query = """
    SELECT 
        cu.segment,
        c.quarter,
        SUM(oi.net_amount) AS revenue
    FROM orders o
    JOIN customers cu ON o.customer_id = cu.customer_id
    JOIN calendar_dim c ON o.order_date_only = c.date_key
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE c.year = 2024 AND c.quarter IN (2, 3)
    GROUP BY cu.segment, c.quarter;
    """
    df = db_con.execute(query).df()

    engine = SegmentationEngine()
    decomp = engine.decompose_movement(
        df=df,
        dimension_col="segment",
        period_col="quarter",
        value_col="revenue",
        period_1=2,
        period_2=3,
        metric_name="revenue",
    )

    assert decomp.total_delta < 0  # Decline in revenue
    assert "Enterprise" in decomp.primary_drivers
    ent_contrib = next(s for s in decomp.segments if s.segment == "Enterprise")
    # Enterprise should account for large share of the drop
    assert ent_contrib.contribution_percentage > 40.0
