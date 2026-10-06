"""Analyses router providing endpoints for creation, state, events, and HITL."""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.orchestrator.context import AnalysisContext, AnalysisState
from core.orchestrator.pipeline import AutonomousDataScientistPipeline
from core.db.duckdb_engine import DuckDBEngine
from core.hitl.manager import HITLDecision
from warehouse.generator import create_in_memory_warehouse

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])

# In-memory storage for active analyses
ANALYSES_STORE: Dict[str, AnalysisContext] = {}

# Shared in-memory warehouse engine
_SHARED_DB_CON = None

def get_shared_engine() -> DuckDBEngine:
    global _SHARED_DB_CON
    if _SHARED_DB_CON is None:
        _SHARED_DB_CON = create_in_memory_warehouse(seed=42)
    return DuckDBEngine(connection=_SHARED_DB_CON)


class CreateAnalysisRequest(BaseModel):
    question: str
    auto_approve_hitl: bool = True


class CreateAnalysisResponse(BaseModel):
    analysis_id: str
    question: str
    status: str
    message: str


def run_pipeline_task(analysis_id: str, question: str, auto_approve: bool):
    engine = get_shared_engine()
    pipeline = AutonomousDataScientistPipeline(engine=engine)
    # Execute investigation
    ctx = pipeline.run_investigation(question=question, auto_approve_hitl=auto_approve)
    # Store updated context under analysis_id
    ctx.analysis_id = analysis_id
    ANALYSES_STORE[analysis_id] = ctx


@router.post("", response_model=CreateAnalysisResponse)
def create_analysis(req: CreateAnalysisRequest, background_tasks: BackgroundTasks):
    """Launch a new autonomous data science investigation."""
    # Pre-create context
    initial_ctx = AnalysisContext(question=req.question)
    analysis_id = initial_ctx.analysis_id
    ANALYSES_STORE[analysis_id] = initial_ctx

    # Run in background
    background_tasks.add_task(run_pipeline_task, analysis_id, req.question, req.auto_approve_hitl)

    return CreateAnalysisResponse(
        analysis_id=analysis_id,
        question=req.question,
        status="RUNNING",
        message="Investigation initiated in background.",
    )


@router.get("/{analysis_id}")
def get_analysis_state(analysis_id: str):
    """Retrieve full analysis status, state machine progress, and final report."""
    ctx = ANALYSES_STORE.get(analysis_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")

    return {
        "analysis_id": ctx.analysis_id,
        "question": ctx.question,
        "current_state": ctx.current_state.value,
        "created_at": ctx.created_at,
        "updated_at": ctx.updated_at,
        "current_step": ctx.current_step,
        "intent": ctx.intent,
        "semantic_context": ctx.semantic_context,
        "investigation_plan": ctx.investigation_plan,
        "active_sql": ctx.active_sql,
        "sql_validation": ctx.sql_validation,
        "cost_estimate": ctx.cost_estimate,
        "query_results_summary": ctx.query_results.get("summary"),
        "hypotheses": ctx.hypotheses,
        "segment_contributions": ctx.segment_contributions,
        "anomalies": ctx.anomalies,
        "causal_inference": ctx.causal_inference,
        "visualizations": ctx.visualizations,
        "critique_findings": ctx.critique_findings,
        "calibrated_confidence": ctx.calibrated_confidence,
        "final_report": ctx.final_report,
        "hitl_checkpoint": ctx.hitl_checkpoint,
        "trajectory_event_count": len(ctx.trajectory),
    }


@router.get("/{analysis_id}/events")
async def stream_analysis_events(analysis_id: str):
    """Stream real-time Server-Sent Events (SSE) for the analysis trajectory."""
    ctx = ANALYSES_STORE.get(analysis_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")

    async def event_generator():
        last_index = 0
        while True:
            current_events = ctx.trajectory[last_index:]
            for ev in current_events:
                yield f"data: {ev.json()}\n\n"
                last_index += 1

            if ctx.current_state in [AnalysisState.COMPLETE, AnalysisState.FAILED, AnalysisState.HUMAN_REVIEW_REQUIRED]:
                # Send terminal message
                yield f"event: done\ndata: {{\"state\": \"{ctx.current_state.value}\"}}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{analysis_id}/evidence")
def get_analysis_evidence(analysis_id: str):
    """Retrieve cryptographic evidence objects backing analytical claims."""
    ctx = ANALYSES_STORE.get(analysis_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")
    return {"analysis_id": analysis_id, "evidence_items": ctx.evidence_store}


@router.post("/{analysis_id}/approve")
def submit_hitl_approval(analysis_id: str, decision: HITLDecision):
    """Submit Human-in-the-Loop decision to resume or complete analysis."""
    ctx = ANALYSES_STORE.get(analysis_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Analysis ID not found.")

    engine = get_shared_engine()
    pipeline = AutonomousDataScientistPipeline(engine=engine)
    updated_ctx = pipeline.hitl_manager.apply_decision(ctx, decision)
    ANALYSES_STORE[analysis_id] = updated_ctx

    return {
        "analysis_id": analysis_id,
        "decision_applied": decision.decision,
        "new_state": updated_ctx.current_state.value,
    }
