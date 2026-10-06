"""Unit tests for Explicit State Machine and Orchestrator."""

import pytest
from core.orchestrator.context import AnalysisState, AnalysisContext
from core.orchestrator.state_machine import StateMachine, TransitionGuardError


def test_state_machine_valid_initial_transitions():
    """Verify valid initial sequence of state transitions."""
    sm = StateMachine()
    ctx = AnalysisContext(question="Why did our revenue decline 8% this quarter?")

    assert ctx.current_state == AnalysisState.QUESTION_RECEIVED

    # 1. QUESTION_RECEIVED -> INTENT_PARSED
    sm.transition(ctx, AnalysisState.INTENT_PARSED, phase="INTERPRET", action="Parsed question intent")
    assert ctx.current_state == AnalysisState.INTENT_PARSED
    assert len(ctx.trajectory) == 1

    # 2. INTENT_PARSED -> SEMANTIC_GROUNDED
    ctx.intent = {"metric": "revenue", "target_period": "Q3 2024", "comparison_period": "Q2 2024"}
    sm.transition(ctx, AnalysisState.SEMANTIC_GROUNDED, phase="GROUND", action="Matched revenue metric")
    assert ctx.current_state == AnalysisState.SEMANTIC_GROUNDED


def test_state_machine_illegal_leap_rejected():
    """Verify illegal leap across states is blocked by transition graph."""
    sm = StateMachine()
    ctx = AnalysisContext(question="Why did revenue drop?")

    # Illegal leap straight to QUERY_EXECUTED
    with pytest.raises(TransitionGuardError) as exc_info:
        sm.transition(ctx, AnalysisState.QUERY_EXECUTED, phase="ACT", action="Premature execution leap")
    assert "Invalid transition" in str(exc_info.value)


def test_state_machine_guard_empty_question():
    """Verify guard blocks empty question from moving to INTENT_PARSED."""
    sm = StateMachine()
    ctx = AnalysisContext(question="   ")

    with pytest.raises(TransitionGuardError) as exc_info:
        sm.transition(ctx, AnalysisState.INTENT_PARSED, phase="INTERPRET", action="Parse")
    assert "Question is empty" in str(exc_info.value)


def test_state_machine_sql_validation_guard():
    """Verify cannot transition to QUERY_COST_ESTIMATED if SQL validation failed."""
    sm = StateMachine()
    ctx = AnalysisContext(question="Why did revenue drop?")
    ctx.intent = {"metric": "revenue"}
    ctx.semantic_context = {"metric": "revenue"}
    ctx.investigation_plan = [{"step": 1}]
    ctx.active_sql = "SELECT * FROM orders"
    ctx.sql_validation = {"is_valid": False, "errors": ["Syntax error"]}

    # Advance to SQL_DRAFTED then SQL_VALIDATED
    ctx.current_state = AnalysisState.SQL_VALIDATED

    with pytest.raises(TransitionGuardError) as exc_info:
        sm.transition(ctx, AnalysisState.QUERY_COST_ESTIMATED, phase="VERIFY", action="Cost check")
    assert "SQL validation failed" in str(exc_info.value)


def test_analysis_context_bounds_check():
    """Verify execution limits guard against infinite loops."""
    ctx = AnalysisContext(question="Test question", max_steps=5)
    ctx.current_step = 6
    ok, err = ctx.check_bounds()
    assert ok is False
    assert "Maximum step count" in err
