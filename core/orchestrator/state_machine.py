"""Finite State Machine and Machine-Checkable Transition Guards."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any, Callable
from core.orchestrator.context import AnalysisState, AnalysisContext, TrajectoryEvent


class TransitionGuardError(Exception):
    """Raised when a state transition violates its pre-conditions."""
    pass


class StateMachine:
    """Manages verified state transitions with machine-checkable guards."""

    def __init__(self):
        # Allowable state transitions graph
        self.transitions: Dict[AnalysisState, List[AnalysisState]] = {
            AnalysisState.QUESTION_RECEIVED: [AnalysisState.INTENT_PARSED, AnalysisState.FAILED],
            AnalysisState.INTENT_PARSED: [AnalysisState.SEMANTIC_GROUNDED, AnalysisState.FAILED],
            AnalysisState.SEMANTIC_GROUNDED: [AnalysisState.PLAN_CREATED, AnalysisState.FAILED],
            AnalysisState.PLAN_CREATED: [AnalysisState.SQL_DRAFTED, AnalysisState.FAILED],
            AnalysisState.SQL_DRAFTED: [AnalysisState.SQL_VALIDATED, AnalysisState.FAILED],
            AnalysisState.SQL_VALIDATED: [
                AnalysisState.QUERY_COST_ESTIMATED,
                AnalysisState.SQL_DRAFTED,  # Rework on invalid SQL
                AnalysisState.FAILED,
            ],
            AnalysisState.QUERY_COST_ESTIMATED: [
                AnalysisState.QUERY_EXECUTED,
                AnalysisState.HUMAN_REVIEW_REQUIRED,  # If cost exceeds safety limit
                AnalysisState.SQL_DRAFTED,  # Optimize query
                AnalysisState.FAILED,
            ],
            AnalysisState.QUERY_EXECUTED: [AnalysisState.DATA_PROFILED, AnalysisState.FAILED],
            AnalysisState.DATA_PROFILED: [AnalysisState.HYPOTHESES_GENERATED, AnalysisState.FAILED],
            AnalysisState.HYPOTHESES_GENERATED: [AnalysisState.HYPOTHESES_RANKED, AnalysisState.FAILED],
            AnalysisState.HYPOTHESES_RANKED: [AnalysisState.HYPOTHESIS_TESTED, AnalysisState.FAILED],
            AnalysisState.HYPOTHESIS_TESTED: [AnalysisState.SEGMENTS_ANALYZED, AnalysisState.FAILED],
            AnalysisState.SEGMENTS_ANALYZED: [AnalysisState.ANOMALIES_DETECTED, AnalysisState.FAILED],
            AnalysisState.ANOMALIES_DETECTED: [AnalysisState.CAUSALITY_ASSESSED, AnalysisState.FAILED],
            AnalysisState.CAUSALITY_ASSESSED: [AnalysisState.VISUALS_CREATED, AnalysisState.FAILED],
            AnalysisState.VISUALS_CREATED: [AnalysisState.CRITIQUE_COMPLETED, AnalysisState.FAILED],
            AnalysisState.CRITIQUE_COMPLETED: [
                AnalysisState.EVIDENCE_VERIFIED,
                AnalysisState.PLAN_CREATED,  # Critic forces rework
                AnalysisState.SQL_DRAFTED,
                AnalysisState.HUMAN_REVIEW_REQUIRED,
                AnalysisState.FAILED,
            ],
            AnalysisState.EVIDENCE_VERIFIED: [AnalysisState.REPORT_DRAFTED, AnalysisState.FAILED],
            AnalysisState.REPORT_DRAFTED: [
                AnalysisState.HUMAN_REVIEW_REQUIRED,
                AnalysisState.COMPLETE,
                AnalysisState.FAILED,
            ],
            AnalysisState.HUMAN_REVIEW_REQUIRED: [
                AnalysisState.COMPLETE,
                AnalysisState.PLAN_CREATED,
                AnalysisState.QUERY_EXECUTED,
                AnalysisState.FAILED,
            ],
            AnalysisState.COMPLETE: [],
            AnalysisState.FAILED: [],
        }

    def validate_transition(
        self,
        from_state: AnalysisState,
        to_state: AnalysisState,
        context: AnalysisContext,
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate both graph connectivity and deterministic semantic guards."""
        # 1. Graph connectivity check
        allowed = self.transitions.get(from_state, [])
        if to_state not in allowed:
            return (
                False,
                f"Invalid transition: Cannot move from {from_state.value} to {to_state.value}. "
                f"Allowed target states: {[s.value for s in allowed]}.",
            )

        # 2. State-specific pre-condition guards
        if to_state == AnalysisState.INTENT_PARSED:
            if not context.question or not context.question.strip():
                return False, "Guard failure: Question is empty."

        elif to_state == AnalysisState.SEMANTIC_GROUNDED:
            if not context.intent:
                return False, "Guard failure: Intent dictionary is missing."

        elif to_state == AnalysisState.PLAN_CREATED:
            if not context.semantic_context:
                return False, "Guard failure: Semantic grounding context is missing."

        elif to_state == AnalysisState.SQL_DRAFTED:
            if not context.investigation_plan:
                return False, "Guard failure: Investigation plan has no steps."

        elif to_state == AnalysisState.SQL_VALIDATED:
            if not context.active_sql:
                return False, "Guard failure: active_sql is not set."

        elif to_state == AnalysisState.QUERY_COST_ESTIMATED:
            if not context.sql_validation.get("is_valid"):
                return False, f"Guard failure: SQL validation failed. Errors: {context.sql_validation.get('errors')}"

        elif to_state == AnalysisState.QUERY_EXECUTED:
            if context.cost_estimate and context.cost_estimate.get("exceeds_threshold"):
                return False, "Guard failure: Query cost exceeds limit without human approval."

        elif to_state == AnalysisState.DATA_PROFILED:
            if not context.query_results:
                return False, "Guard failure: Query results are missing."

        elif to_state == AnalysisState.HYPOTHESES_RANKED:
            if not context.hypotheses:
                return False, "Guard failure: No hypotheses were generated to rank."

        elif to_state == AnalysisState.EVIDENCE_VERIFIED:
            if not context.critique_findings:
                return False, "Guard failure: Critique findings must be recorded before evidence verification."

        elif to_state == AnalysisState.COMPLETE:
            if not context.final_report:
                return False, "Guard failure: Final analyst report has not been drafted."
            if context.calibrated_confidence <= 0.0:
                return False, "Guard failure: Calibrated confidence score must be calculated."

        return True, None

    def transition(
        self,
        context: AnalysisContext,
        to_state: AnalysisState,
        phase: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        tokens: int = 0,
    ) -> TrajectoryEvent:
        """Execute a guarded state transition and append to trajectory."""
        is_valid, err = self.validate_transition(context.current_state, to_state, context)
        if not is_valid:
            # Check retries for current state
            state_key = context.current_state.value
            retries = context.retries_per_state.get(state_key, 0)
            if retries < context.max_retries_per_state and to_state != AnalysisState.FAILED:
                context.retries_per_state[state_key] = retries + 1
                raise TransitionGuardError(f"Guard rejected transition: {err} (Retry {retries + 1}/{context.max_retries_per_state})")
            else:
                # Exceeded retries: transition to FAILED
                fail_event = context.record_event(
                    to_state=AnalysisState.FAILED,
                    phase="GUARD_FAILURE",
                    action=f"Failed transitioning to {to_state.value}: {err}",
                    details={"error": err, "last_state": context.current_state.value},
                )
                raise TransitionGuardError(f"Fatal transition failure: {err}")

        # Record valid transition
        return context.record_event(
            from_state=context.current_state,
            to_state=to_state,
            phase=phase,
            action=action,
            details=details,
            duration_ms=duration_ms,
            tokens=tokens,
        )
