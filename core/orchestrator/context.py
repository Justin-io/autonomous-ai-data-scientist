"""Analysis Context and Trajectory Storage."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class AnalysisState(str, Enum):
    QUESTION_RECEIVED = "QUESTION_RECEIVED"
    INTENT_PARSED = "INTENT_PARSED"
    SEMANTIC_GROUNDED = "SEMANTIC_GROUNDED"
    PLAN_CREATED = "PLAN_CREATED"
    SQL_DRAFTED = "SQL_DRAFTED"
    SQL_VALIDATED = "SQL_VALIDATED"
    QUERY_COST_ESTIMATED = "QUERY_COST_ESTIMATED"
    QUERY_EXECUTED = "QUERY_EXECUTED"
    DATA_PROFILED = "DATA_PROFILED"
    HYPOTHESES_GENERATED = "HYPOTHESES_GENERATED"
    HYPOTHESES_RANKED = "HYPOTHESES_RANKED"
    HYPOTHESIS_TESTED = "HYPOTHESIS_TESTED"
    SEGMENTS_ANALYZED = "SEGMENTS_ANALYZED"
    ANOMALIES_DETECTED = "ANOMALIES_DETECTED"
    CAUSALITY_ASSESSED = "CAUSALITY_ASSESSED"
    VISUALS_CREATED = "VISUALS_CREATED"
    CRITIQUE_COMPLETED = "CRITIQUE_COMPLETED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    REPORT_DRAFTED = "REPORT_DRAFTED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class TrajectoryEvent(BaseModel):
    """Immutable audit record of a single step or transition in the trajectory."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    from_state: Optional[AnalysisState]
    to_state: AnalysisState
    phase: str  # OBSERVE, PLAN, ACT, VERIFY, CRITIQUE, RECORD, etc.
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    duration_ms: float = 0.0


class AnalysisContext(BaseModel):
    """Durable state container for an autonomous data science investigation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    current_state: AnalysisState = AnalysisState.QUESTION_RECEIVED
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    # Structured Payloads
    intent: Dict[str, Any] = Field(default_factory=dict)
    semantic_context: Dict[str, Any] = Field(default_factory=dict)
    investigation_plan: List[Dict[str, Any]] = Field(default_factory=list)
    active_sql: Optional[str] = None
    sql_validation: Dict[str, Any] = Field(default_factory=dict)
    cost_estimate: Dict[str, Any] = Field(default_factory=dict)
    query_results: Dict[str, Any] = Field(default_factory=dict)
    data_profile: Dict[str, Any] = Field(default_factory=dict)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    segment_contributions: Dict[str, Any] = Field(default_factory=dict)
    anomalies: Dict[str, Any] = Field(default_factory=dict)
    causal_inference: Dict[str, Any] = Field(default_factory=dict)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    critique_findings: Dict[str, Any] = Field(default_factory=dict)
    evidence_store: List[Dict[str, Any]] = Field(default_factory=list)
    calibrated_confidence: float = 0.0
    final_report: Optional[str] = None

    # Human-In-The-Loop
    hitl_checkpoint: Optional[Dict[str, Any]] = None
    hitl_decision: Optional[str] = None  # "APPROVED", "REJECTED", "MODIFIED"

    # Execution Bounds and Telemetry
    max_steps: int = 50
    current_step: int = 0
    max_execution_time_sec: float = 300.0
    max_tool_calls: int = 100
    tool_call_count: int = 0
    total_tokens: int = 0
    total_query_cost: float = 0.0
    retries_per_state: Dict[str, int] = Field(default_factory=dict)
    max_retries_per_state: int = 3
    trajectory: List[TrajectoryEvent] = Field(default_factory=list)

    def record_event(
        self,
        to_state: AnalysisState,
        phase: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        from_state: Optional[AnalysisState] = None,
        duration_ms: float = 0.0,
        tokens: int = 0,
    ) -> TrajectoryEvent:
        """Append an immutable trajectory event and update timestamps."""
        event = TrajectoryEvent(
            from_state=from_state or self.current_state,
            to_state=to_state,
            phase=phase,
            action=action,
            details=details or {},
            tokens_used=tokens,
            duration_ms=duration_ms,
        )
        self.trajectory.append(event)
        self.current_state = to_state
        self.updated_at = time.time()
        self.current_step += 1
        self.total_tokens += tokens
        return event

    def check_bounds(self) -> Tuple[bool, Optional[str]]:
        """Verify execution has not exceeded safety limits."""
        if self.current_step > self.max_steps:
            return False, f"Maximum step count ({self.max_steps}) exceeded. Stopping to prevent infinite loop."
        if (time.time() - self.created_at) > self.max_execution_time_sec:
            return False, f"Maximum execution time ({self.max_execution_time_sec}s) exceeded."
        if self.tool_call_count > self.max_tool_calls:
            return False, f"Maximum tool calls ({self.max_tool_calls}) exceeded."
        return True, None
