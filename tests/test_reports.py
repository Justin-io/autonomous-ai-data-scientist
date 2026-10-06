"""Unit tests for Visuals, Reports, and HITL management."""

import pytest
import pandas as pd
from core.orchestrator.context import AnalysisContext, AnalysisState
from core.evidence.store import EvidenceStore
from core.evidence.confidence import ConfidenceScorer
from core.visuals.generator import PlotlyVisualGenerator
from core.report.generator import AnalystReportGenerator
from core.hitl.manager import HITLManager, HITLDecision
from core.statistics.segmentation import SegmentContribution, SegmentationDecompositionResult


def test_plotly_waterfall_generation():
    """Verify Plotly waterfall visualization spec."""
    decomp = SegmentationDecompositionResult(
        dimension="segment",
        metric="revenue",
        total_period_1=4040549.0,
        total_period_2=3736122.0,
        total_delta=-304427.0,
        total_percentage_change=-7.53,
        segments=[
            SegmentContribution(
                segment="Enterprise",
                period_1_value=1500000.0,
                period_2_value=1170000.0,
                absolute_delta=-330000.0,
                percentage_change=-22.0,
                contribution_percentage=108.4,
                is_primary_driver=True,
            )
        ],
        primary_drivers=["Enterprise"],
        concentration_hhi=8500.0,
        narrative="Decomposition test",
    )

    gen = PlotlyVisualGenerator()
    spec = gen.create_contribution_waterfall(decomp)

    assert spec.chart_type == "waterfall"
    assert "Waterfall" in spec.title
    assert "data" in spec.plotly_json
    assert len(spec.plotly_json["data"]) > 0


def test_analyst_report_generation():
    """Verify structured analyst report generation with evidence citations."""
    store = EvidenceStore()
    store.add_evidence(
        claim_key="q2_rev",
        numeric_value=4040549.0,
        unit="USD",
        query_sql="SELECT ...",
        query_hash="q2",
        dataset_hash="d2",
        metric_definition="revenue",
    )
    store.add_evidence(
        claim_key="q3_rev",
        numeric_value=3736122.0,
        unit="USD",
        query_sql="SELECT ...",
        query_hash="q3",
        dataset_hash="d3",
        metric_definition="revenue",
    )
    store.add_evidence(
        claim_key="decline_pct",
        numeric_value=-7.5,
        unit="%",
        query_sql="SELECT ...",
        query_hash="q4",
        dataset_hash="d4",
        metric_definition="decline",
    )

    scorer = ConfidenceScorer()
    conf = scorer.calculate_confidence(data_quality=0.98, sample_size=2000, p_value=0.001)

    ctx = AnalysisContext(
        question="Why did our revenue decline 8% this quarter?",
        query_results={
            "summary": {
                "q2_revenue": 4040549.0,
                "q3_revenue": 3736122.0,
                "decline_percentage": -7.5,
            }
        },
        hypotheses=[
            {
                "id": "H-03",
                "statement": "Enterprise churn",
                "category": "SEGMENT_CHURN",
                "prior_probability": 0.25,
                "current_probability": 0.85,
                "status": "CONFIRMED",
            }
        ],
    )

    gen = AnalystReportGenerator()
    report = gen.generate_report(ctx, store, conf)

    assert "# Executive Analytical Report" in report
    assert "1. Executive Answer & Core Findings" in report
    assert "3. Autonomous Hypothesis Investigation" in report
    assert "8. Causal Assessment & Defensive Downgrading" in report
    assert "12. Complete Evidence Lineage Catalog" in report
    assert "[EVD-" in report  # Contains evidence citations


def test_hitl_manager_triggers_and_decision():
    """Verify HITL trigger evaluation and decision application."""
    mgr = HITLManager(confidence_threshold=0.70)
    ctx = AnalysisContext(
        question="Why did revenue drop?",
        calibrated_confidence=0.55,  # Below threshold
    )

    should_trigger, reasons = mgr.evaluate_triggers(ctx)
    assert should_trigger is True
    assert any("below safety threshold" in r for r in reasons)

    packet = mgr.build_review_packet(ctx, reasons)
    assert packet.analysis_id == ctx.analysis_id
    assert len(packet.trigger_reasons) > 0

    # Test approval
    decision = HITLDecision(decision="APPROVED", reviewer_notes="Approved by CFO")
    updated_ctx = mgr.apply_decision(ctx, decision)
    assert updated_ctx.current_state == AnalysisState.COMPLETE
    assert updated_ctx.hitl_decision == "APPROVED"
