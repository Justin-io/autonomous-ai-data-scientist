"""Plotly Visualization Generator based on Analytical Intent."""

from __future__ import annotations

import json
from typing import Dict, Any, List, Optional
import pandas as pd
from pydantic import BaseModel, Field
import plotly.graph_objects as go

from core.statistics.segmentation import SegmentationDecompositionResult
from core.statistics.anomalies import AnomalyPoint


class VisualizationSpec(BaseModel):
    """Specification of an interactive Plotly chart."""

    chart_id: str
    chart_type: str  # waterfall, time_series, grouped_bar, scatter
    title: str
    intent: str
    plotly_json: Dict[str, Any]


class PlotlyVisualGenerator:
    """Generates clean, intent-tailored Plotly visualizations."""

    def create_contribution_waterfall(
        self,
        decomposition: SegmentationDecompositionResult,
    ) -> VisualizationSpec:
        """Generate a waterfall chart decomposing total metric change by segment."""
        categories = ["Baseline (P1)"]
        values = [decomposition.total_period_1]
        measures = ["absolute"]

        for s in decomposition.segments:
            categories.append(s.segment)
            values.append(s.absolute_delta)
            measures.append("relative")

        categories.append("Current (P2)")
        values.append(decomposition.total_period_2)
        measures.append("total")

        fig = go.Figure(
            go.Waterfall(
                name="Contribution",
                orientation="v",
                measure=measures,
                x=categories,
                textposition="outside",
                text=[f"${v:+,.0f}" if m == "relative" else f"${v:,.0f}" for v, m in zip(values, measures)],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#10B981"}},
                decreasing={"marker": {"color": "#EF4444"}},
                totals={"marker": {"color": "#3B82F6"}},
            )
        )
        fig.update_layout(
            title=f"Shift-Share Contribution: {decomposition.metric.capitalize()} Variance by {decomposition.dimension.capitalize()}",
            waterfallgap=0.3,
            template="plotly_white",
            yaxis_title=f"{decomposition.metric.capitalize()} ($)",
            height=450,
        )

        return VisualizationSpec(
            chart_id=f"chart-waterfall-{decomposition.dimension}",
            chart_type="waterfall",
            title=f"{decomposition.dimension.capitalize()} Contribution Waterfall",
            intent=f"Decompose overall {decomposition.metric} movement into segment delta contributions",
            plotly_json=json.loads(fig.to_json()),
        )

    def create_time_series_with_anomalies(
        self,
        df: pd.DataFrame,
        date_col: str,
        val_col: str,
        anomalies: List[AnomalyPoint],
        title: str = "Time Series Trend with Detected Anomalies",
    ) -> VisualizationSpec:
        """Generate time-series line chart with highlighted anomaly markers."""
        df_sorted = df.sort_values(date_col)

        fig = go.Figure()
        # Baseline line
        fig.add_trace(
            go.Scatter(
                x=df_sorted[date_col],
                y=df_sorted[val_col],
                mode="lines+markers",
                name="Actual",
                line={"color": "#2563EB", "width": 2},
                marker={"size": 4},
            )
        )

        # Anomaly markers
        if anomalies:
            anom_x = [a.label for a in anomalies]
            anom_y = [a.value for a in anomalies]
            anom_text = [f"<b>{a.severity} ANOMALY</b><br>{a.explanation}" for a in anomalies]

            fig.add_trace(
                go.Scatter(
                    x=anom_x,
                    y=anom_y,
                    mode="markers",
                    name="Detected Anomalies",
                    marker={"size": 12, "color": "#DC2626", "symbol": "diamond", "line": {"width": 2, "color": "white"}},
                    text=anom_text,
                    hoverinfo="text",
                )
            )

        fig.update_layout(
            title=title,
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title=val_col.replace("_", " ").title(),
            height=450,
        )

        return VisualizationSpec(
            chart_id="chart-timeseries-anomalies",
            chart_type="time_series",
            title=title,
            intent="Track temporal progression and isolate anomalous outlier points",
            plotly_json=json.loads(fig.to_json()),
        )

    def create_simpsons_paradox_comparison(
        self,
        stratified_df: pd.DataFrame,
        aggregate_df: pd.DataFrame,
    ) -> VisualizationSpec:
        """Create a stratified comparison bar chart demonstrating Simpson's Paradox."""
        fig = go.Figure()

        # Add Subgroups (e.g. Desktop, Mobile)
        devices = stratified_df["device"].unique()
        for variant in ["control_A", "treatment_B"]:
            v_data = stratified_df[stratified_df["variant"] == variant]
            rates = [float(v_data[v_data["device"] == d]["conversion_rate"].iloc[0]) * 100.0 for d in devices]
            fig.add_trace(
                go.Bar(
                    name=f"{variant.replace('_', ' ').title()}",
                    x=[f"{d.capitalize()} Subgroup" for d in devices],
                    y=rates,
                    text=[f"{r:.1f}%" for r in rates],
                    textposition="auto",
                )
            )

        # Add Aggregate bars
        for variant in ["control_A", "treatment_B"]:
            agg_rate = float(aggregate_df[aggregate_df["variant"] == variant]["conversion_rate"].iloc[0]) * 100.0
            fig.add_trace(
                go.Bar(
                    name=f"Aggregate {variant.replace('_', ' ').title()}",
                    x=["AGGREGATE (Confounded)"],
                    y=[agg_rate],
                    text=[f"{agg_rate:.1f}%"],
                    textposition="auto",
                    showlegend=False,
                )
            )

        fig.update_layout(
            title="Simpson's Paradox: Aggregate Lift vs Stratified Subgroup Reversal",
            barmode="group",
            template="plotly_white",
            yaxis_title="Conversion Rate (%)",
            height=450,
        )

        return VisualizationSpec(
            chart_id="chart-simpsons-paradox",
            chart_type="grouped_bar",
            title="Simpson's Paradox Analysis",
            intent="Illustrate how confounding traffic mix reverses apparent treatment superiority",
            plotly_json=json.loads(fig.to_json()),
        )
