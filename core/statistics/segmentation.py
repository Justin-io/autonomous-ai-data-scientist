"""Multi-Dimensional Segmentation and Shift-Share Contribution Decomposition."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import pandas as pd
from pydantic import BaseModel, Field


class SegmentContribution(BaseModel):
    """Contribution of an individual slice to total variance."""

    segment: str
    period_1_value: float
    period_2_value: float
    absolute_delta: float
    percentage_change: float
    contribution_percentage: float  # Share of total change explained
    is_primary_driver: bool  # Explains > 40% of change


class SegmentationDecompositionResult(BaseModel):
    """Decomposition result across a given dimension."""

    dimension: str
    metric: str
    total_period_1: float
    total_period_2: float
    total_delta: float
    total_percentage_change: float
    segments: List[SegmentContribution]
    primary_drivers: List[str]
    concentration_hhi: float  # Herfindahl-Hirschman index of contribution concentration
    narrative: str


class SegmentationEngine:
    """Decomposes overall metric variance across categorical dimensions."""

    def decompose_movement(
        self,
        df: pd.DataFrame,
        dimension_col: str,
        period_col: str,
        value_col: str,
        period_1: Any,
        period_2: Any,
        metric_name: str = "revenue",
    ) -> SegmentationDecompositionResult:
        """Calculate shift-share contribution percentage for each segment."""
        # Filter for periods
        df_p1 = df[df[period_col] == period_1]
        df_p2 = df[df[period_col] == period_2]

        p1_agg = df_p1.groupby(dimension_col)[value_col].sum().to_dict()
        p2_agg = df_p2.groupby(dimension_col)[value_col].sum().to_dict()

        all_segments = sorted(list(set(list(p1_agg.keys()) + list(p2_agg.keys()))))
        total_p1 = sum(p1_agg.values())
        total_p2 = sum(p2_agg.values())
        total_delta = total_p2 - total_p1
        total_pct_change = (total_delta / max(1e-6, total_p1)) * 100.0

        segment_contributions = []
        primary_drivers = []
        shares_squared = 0.0

        for seg in all_segments:
            v1 = float(p1_agg.get(seg, 0.0))
            v2 = float(p2_agg.get(seg, 0.0))
            delta = v2 - v1
            pct_change = ((v2 - v1) / max(1e-6, v1)) * 100.0

            # Contribution share to total delta
            if abs(total_delta) > 1e-6:
                contrib_pct = (delta / total_delta) * 100.0
            else:
                contrib_pct = 0.0

            # Primary driver if it explains > 40% of the movement in same direction
            is_driver = (contrib_pct >= 40.0) if total_delta < 0 else (contrib_pct >= 40.0)
            if is_driver:
                primary_drivers.append(str(seg))

            # Concentration HHI (normalized 0 to 10000)
            if abs(total_delta) > 1e-6:
                share_frac = abs(delta) / max(1e-6, sum(abs(v2 - v1) for s in all_segments))
                shares_squared += (share_frac * 100.0) ** 2

            segment_contributions.append(
                SegmentContribution(
                    segment=str(seg),
                    period_1_value=round(v1, 2),
                    period_2_value=round(v2, 2),
                    absolute_delta=round(delta, 2),
                    percentage_change=round(pct_change, 2),
                    contribution_percentage=round(contrib_pct, 2),
                    is_primary_driver=is_driver,
                )
            )

        # Sort segments by absolute delta descending
        segment_contributions.sort(key=lambda s: abs(s.absolute_delta), reverse=True)

        # Synthesis narrative
        if primary_drivers:
            driver_str = ", ".join(f"'{d}'" for d in primary_drivers)
            top_seg = segment_contributions[0]
            narrative = (
                f"Movement in {metric_name} ({total_pct_change:+.1f}%) is predominantly driven by {driver_str}. "
                f"Specifically, {top_seg.segment} changed by {top_seg.percentage_change:+.1f}% ({top_seg.absolute_delta:+,.0f}), "
                f"explaining {top_seg.contribution_percentage:.1f}% of the overall variance."
            )
        else:
            narrative = (
                f"Movement in {metric_name} ({total_pct_change:+.1f}%) was broadly distributed across "
                f"all {len(all_segments)} segments without a single dominant driver."
            )

        return SegmentationDecompositionResult(
            dimension=dimension_col,
            metric=metric_name,
            total_period_1=round(total_p1, 2),
            total_period_2=round(total_p2, 2),
            total_delta=round(total_delta, 2),
            total_percentage_change=round(total_pct_change, 2),
            segments=segment_contributions,
            primary_drivers=primary_drivers,
            concentration_hhi=round(shares_squared, 1),
            narrative=narrative,
        )
