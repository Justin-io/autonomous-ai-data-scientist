"""End-to-End and FastAPI Integration Tests."""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from core.orchestrator.pipeline import AutonomousDataScientistPipeline
from core.db.duckdb_engine import DuckDBEngine
from warehouse.generator import create_in_memory_warehouse
from eval.benchmark_suite import BenchmarkCase
from eval.harness import EvaluationHarness


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def shared_db():
    return create_in_memory_warehouse(seed=42)


def test_api_health_and_ready(client):
    """Verify health and readiness probes."""
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_api_semantic_catalog(client):
    """Verify semantic catalog and metrics discovery endpoints."""
    res = client.get("/api/v1/semantic/catalog")
    assert res.status_code == 200
    catalog_data = res.json()
    assert "revenue" in catalog_data["metrics"]
    assert "customers" in catalog_data["entities"]

    res_metrics = client.get("/api/v1/semantic/metrics")
    assert res_metrics.status_code == 200
    assert len(res_metrics.json()) >= 5


def test_end_to_end_bq1_revenue_decline_pipeline(shared_db):
    """Verify complete end-to-end autonomous investigation of BQ-1."""
    engine = DuckDBEngine(connection=shared_db)
    pipeline = AutonomousDataScientistPipeline(engine=engine)

    question = "Why did our revenue decline 8% this quarter?"
    ctx = pipeline.run_investigation(question=question, auto_approve_hitl=True)

    # 1. Pipeline should successfully complete
    assert ctx.current_state.value in ["COMPLETE", "HUMAN_REVIEW_REQUIRED"]
    assert len(ctx.trajectory) >= 15

    # 2. Key findings and shift-share decomposition
    assert len(ctx.evidence_store) >= 3
    assert ctx.calibrated_confidence >= 0.70

    # 3. Final report structure
    report = ctx.final_report
    assert report is not None
    assert "# Executive Analytical Report" in report
    assert "[EVD-" in report  # Contains evidence citations
    assert "Enterprise" in report  # Identifies Enterprise root cause


def test_evaluation_harness_bq1(shared_db):
    """Verify evaluation harness scoring on BQ-1 benchmark case."""
    engine = DuckDBEngine(connection=shared_db)
    pipeline = AutonomousDataScientistPipeline(engine=engine)
    harness = EvaluationHarness(pipeline=pipeline)

    case = BenchmarkCase(
        id="BQ-1",
        question="Why did our revenue decline 8% this quarter?",
        target_metric="revenue",
        scenario_type="REVENUE_DECLINE",
        expected_primary_driver="Enterprise",
    )

    score = harness.run_benchmark_case(case)
    assert score.task_success is True
    assert score.semantic_grounding_accuracy >= 0.95
    assert score.sql_validity == 1.0
    assert score.read_only_safety == 1.0
    assert score.unsupported_claim_rate == 0.0
    assert score.citation_coverage_rate == 1.0
