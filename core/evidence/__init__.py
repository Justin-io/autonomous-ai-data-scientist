"""Evidence store and verification module."""

from core.evidence.store import EvidenceItem, EvidenceStore
from core.evidence.confidence import (
    ConfidenceFactors,
    CalibratedConfidenceResult,
    ConfidenceScorer,
)
from core.evidence.verifier import (
    VerifiedClaim,
    VerificationReport,
    EvidenceVerifier,
)

__all__ = [
    "EvidenceItem",
    "EvidenceStore",
    "ConfidenceFactors",
    "CalibratedConfidenceResult",
    "ConfidenceScorer",
    "VerifiedClaim",
    "VerificationReport",
    "EvidenceVerifier",
]
