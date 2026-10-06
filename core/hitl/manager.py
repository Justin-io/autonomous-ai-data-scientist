"""Human-In-The-Loop (HITL) Checkpoints and Review Manager."""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.orchestrator.context import AnalysisContext, AnalysisState


class HITLReviewPacket(BaseModel):
    """Complete context packet presented to human reviewer during an approval pause."""

    analysis_id: str
    question: str
    trigger_reasons: List[str]
    interpreted_question: str
    proposed_plan: List[Dict[str, Any]]
    semantic_assumptions: Dict[str, Any]
    generated_sql: Optional[str]
    query_cost_estimate: Dict[str, Any]
    hypotheses: List[Dict[str, Any]]
    rejected_hypotheses: List[Dict[str, Any]]
    critic_objections: List[Dict[str, Any]]
    calibrated_confidence: float
    required_decision: str
    created_at: float = Field(default_factory=time.time)


class HITLDecision(BaseModel):
    """Human decision payload submitted to resume analysis."""

    decision: str  # "APPROVED", "REJECTED", "MODIFIED"
    reviewer_notes: Optional[str] = None
    modified_plan: Optional[List[Dict[str, Any]]] = None
    modified_sql: Optional[str] = None


class HITLManager:
    """Evaluates approval triggers and manages human sign-off checkpoints."""

    def __init__(self, confidence_threshold: float = 0.70, max_query_cost: float = 100000.0):
        self.confidence_threshold = confidence_threshold
        self.max_query_cost = max_query_cost

    def evaluate_triggers(self, context: AnalysisContext) -> Tuple[bool, List[str]]:
        """Determine whether human approval is strictly required."""
        triggers = []

        # 1. Low calibrated confidence
        if context.calibrated_confidence > 0 and context.calibrated_confidence < self.confidence_threshold:
            triggers.append(
                f"Calibrated confidence ({context.calibrated_confidence:.1%}) is below safety threshold ({self.confidence_threshold:.1%})."
            )

        # 2. Query cost threshold exceeded
        if context.cost_estimate.get("exceeds_threshold"):
            triggers.append(
                f"Estimated query cost ({context.cost_estimate.get('estimated_cost', 0):.0f}) exceeds threshold ({self.max_query_cost:.0f})."
            )

        # 3. Unresolved Critic blocking issues
        if context.critique_findings.get("rework_required"):
            triggers.append("Critic Agent flagged unresolved blocking analytical risks.")

        # 4. High-risk causal recommendation with observational data
        if context.causal_inference.get("claim_type") == "ASSOCIATIVE" and any(
            "pricing" in k.lower() for k in context.intent.keys()
        ):
            triggers.append("High-stakes business policy recommendation requires executive sign-off.")

        return len(triggers) > 0, triggers

    def build_review_packet(self, context: AnalysisContext, triggers: List[str]) -> HITLReviewPacket:
        """Construct structured review packet for the frontend or human reviewer."""
        rejected_hyps = [h for h in context.hypotheses if h.get("status") in ["REFUTED", "HypothesisStatus.REFUTED"]]

        return HITLReviewPacket(
            analysis_id=context.analysis_id,
            question=context.question,
            trigger_reasons=triggers,
            interpreted_question=str(context.intent.get("summary", context.question)),
            proposed_plan=context.investigation_plan,
            semantic_assumptions=context.semantic_context,
            generated_sql=context.active_sql,
            query_cost_estimate=context.cost_estimate,
            hypotheses=context.hypotheses,
            rejected_hypotheses=rejected_hyps,
            critic_objections=context.critique_findings.get("issues", []),
            calibrated_confidence=context.calibrated_confidence,
            required_decision="Confirm whether to accept associative findings and proceed to final publication.",
        )

    def apply_decision(self, context: AnalysisContext, decision_payload: HITLDecision) -> AnalysisContext:
        """Apply human decision and advance or reroute state machine."""
        context.hitl_decision = decision_payload.decision
        if decision_payload.decision == "APPROVED":
            context.record_event(
                to_state=AnalysisState.COMPLETE,
                phase="HUMAN_APPROVAL",
                action="Human operator approved analysis findings",
                details={"notes": decision_payload.reviewer_notes},
            )
        elif decision_payload.decision == "MODIFIED":
            if decision_payload.modified_sql:
                context.active_sql = decision_payload.modified_sql
            context.record_event(
                to_state=AnalysisState.SQL_DRAFTED,
                phase="HUMAN_MODIFICATION",
                action="Human operator provided adjusted plan or SQL",
                details={"notes": decision_payload.reviewer_notes},
            )
        else:
            context.record_event(
                to_state=AnalysisState.FAILED,
                phase="HUMAN_REJECTION",
                action="Human operator rejected analysis trajectory",
                details={"notes": decision_payload.reviewer_notes},
            )
        return context
