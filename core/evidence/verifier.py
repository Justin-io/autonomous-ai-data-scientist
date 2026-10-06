"""Deterministic Evidence Claim Verifier and Hallucination Guard."""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.evidence.store import EvidenceStore, EvidenceItem


class VerifiedClaim(BaseModel):
    """Result of cross-referencing a text claim against EvidenceStore."""

    claim_text: str
    extracted_number: float
    is_verified: bool
    evidence_id: Optional[str] = None
    metric_definition: Optional[str] = None
    dataset_hash: Optional[str] = None
    hallucination_warning: Optional[str] = None


class VerificationReport(BaseModel):
    """Deterministic verification report for a generated narrative."""

    total_claims_detected: int
    verified_claims_count: int
    unsupported_claims_count: int
    unsupported_claim_rate: float
    citation_coverage_rate: float
    passed: bool
    verified_claims: List[VerifiedClaim] = Field(default_factory=list)
    unsupported_claims: List[VerifiedClaim] = Field(default_factory=list)
    summary: str


class EvidenceVerifier:
    """Extracts numeric statements from narrative and deterministically verifies them against EvidenceStore."""

    def __init__(self, evidence_store: EvidenceStore):
        self.evidence_store = evidence_store

    def verify_report(self, text: str, tolerance: float = 0.05) -> VerificationReport:
        """Scan text, extract numbers/percentages, and verify against EvidenceStore."""
        # Regex to capture:
        # 1. Percentages: e.g. "8.2%", "-7.5%", "22%"
        # 2. Currency: e.g. "$4,040,549", "$3,736,122"
        # 3. Explicit citation tags: e.g. "[EVD-12345678]"
        pct_matches = re.finditer(r"([+-]?\d+(?:\.\d+)?)\s*%", text)
        currency_matches = re.finditer(r"\$\s*([0-9,]+(?:\.\d+)?)", text)

        detected_claims = []

        # Process percentages
        for m in pct_matches:
            val = float(m.group(1))
            raw_str = m.group(0)
            # Find matching evidence (also check magnitude if sign differed)
            ev = self.evidence_store.find_matching_evidence(val, tolerance=tolerance)
            if not ev:
                ev = self.evidence_store.find_matching_evidence(abs(val), tolerance=tolerance)

            detected_claims.append((raw_str, val, ev))

        # Process currencies
        for m in currency_matches:
            clean_num = m.group(1).replace(",", "")
            val = float(clean_num)
            raw_str = m.group(0)
            ev = self.evidence_store.find_matching_evidence(val, tolerance=tolerance)
            detected_claims.append((raw_str, val, ev))

        verified = []
        unsupported = []

        for raw_str, val, ev in detected_claims:
            if ev:
                verified.append(
                    VerifiedClaim(
                        claim_text=raw_str,
                        extracted_number=val,
                        is_verified=True,
                        evidence_id=ev.evidence_id,
                        metric_definition=ev.metric_definition,
                        dataset_hash=ev.dataset_hash,
                    )
                )
            else:
                unsupported.append(
                    VerifiedClaim(
                        claim_text=raw_str,
                        extracted_number=val,
                        is_verified=False,
                        hallucination_warning=f"Claim '{raw_str}' ({val}) has no matching evidence record in EvidenceStore.",
                    )
                )

        total = len(detected_claims)
        v_count = len(verified)
        u_count = len(unsupported)
        u_rate = round(u_count / max(1, total), 3)
        c_rate = round(v_count / max(1, total), 3)
        passed = (u_count == 0)

        summary = (
            f"Deterministic Evidence Verification PASSED: {v_count}/{total} numerical claims verified (100% coverage)."
            if passed
            else f"Deterministic Evidence Verification FAILED: {u_count}/{total} numerical claims could not be reconstructed from data (Unsupported claim rate: {u_rate:.1%})."
        )

        return VerificationReport(
            total_claims_detected=total,
            verified_claims_count=v_count,
            unsupported_claims_count=u_count,
            unsupported_claim_rate=u_rate,
            citation_coverage_rate=c_rate,
            passed=passed,
            verified_claims=verified,
            unsupported_claims=unsupported,
            summary=summary,
        )
