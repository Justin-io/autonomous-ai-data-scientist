"""Evaluations router providing benchmark execution and evaluation scoring."""

from __future__ import annotations

from fastapi import APIRouter
from eval.benchmark_suite import get_default_benchmarks
from eval.harness import EvaluationHarness, EvaluationSuiteSummary
from core.orchestrator.pipeline import AutonomousDataScientistPipeline
from api.routes.analyses import get_shared_engine

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


@router.get("/benchmarks")
def list_benchmarks():
    """List canonical evaluation benchmark questions and expected traps."""
    return [b.model_dump() for b in get_default_benchmarks()]


@router.post("/run", response_model=EvaluationSuiteSummary)
def run_evaluation_suite():
    """Run full benchmark evaluation harness across all canonical business questions."""
    engine = get_shared_engine()
    pipeline = AutonomousDataScientistPipeline(engine=engine)
    harness = EvaluationHarness(pipeline=pipeline)
    return harness.run_all()
