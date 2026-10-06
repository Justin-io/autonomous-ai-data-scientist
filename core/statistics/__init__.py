"""Statistics, Anomalies, and Segmentation Package."""

from core.statistics.descriptive import DescriptiveStats, compute_descriptive_stats
from core.statistics.inferential import HypothesisTestResult, InferentialStatsEngine
from core.statistics.anomalies import AnomalyPoint, AnomalyReport, AnomalyDetector
from core.statistics.segmentation import (
    SegmentContribution,
    SegmentationDecompositionResult,
    SegmentationEngine,
)

__all__ = [
    "DescriptiveStats",
    "compute_descriptive_stats",
    "HypothesisTestResult",
    "InferentialStatsEngine",
    "AnomalyPoint",
    "AnomalyReport",
    "AnomalyDetector",
    "SegmentContribution",
    "SegmentationDecompositionResult",
    "SegmentationEngine",
]
