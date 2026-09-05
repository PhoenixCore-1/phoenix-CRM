"""Provider-independent AI intelligence contracts for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerActivity, CustomerFollowUp


class CRMIntelligenceType(str, Enum):
    """Supported CRM AI assistance categories."""

    CUSTOMER_SUMMARY = "customer_summary"
    CALL_PREPARATION = "call_preparation"
    NEXT_BEST_ACTION = "next_best_action"
    RELATIONSHIP_RISK = "relationship_risk"
    ACTIVITY_SUMMARY = "activity_summary"
    LEAD_QUALIFICATION = "lead_qualification"
    POTENTIAL_DETECTION = "potential_detection"


@dataclass(frozen=True, slots=True)
class AIProposal:
    """An AI recommendation that requires authorized human handling."""

    intelligence_type: CRMIntelligenceType
    customer_id: UUID
    summary: str
    rationale: str
    confidence: float | None = None
    proposed_action: str | None = None

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("summary must not be empty")
        if not self.rationale.strip():
            raise ValueError("rationale must not be empty")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


class CRMIntelligenceService:
    """Create deterministic AI input/proposal envelopes without calling a provider."""

    @staticmethod
    def context_for_customer(
        customer: Customer,
        activities: list[CustomerActivity],
        follow_ups: list[CustomerFollowUp],
    ) -> dict[str, object]:
        """Build a minimal tenant-scoped context package for Core AI services."""
        customer_activities = [
            activity for activity in activities
            if activity.tenant_id == customer.tenant_id and activity.customer_id == customer.id
        ]
        customer_follow_ups = [
            follow_up for follow_up in follow_ups
            if follow_up.tenant_id == customer.tenant_id and follow_up.customer_id == customer.id
        ]
        return {
            "customer_id": str(customer.id),
            "tenant_id": str(customer.tenant_id),
            "customer_name": customer.name,
            "customer_type_id": str(customer.customer_type_id),
            "call_class_id": str(customer.call_class_id),
            "status": customer.status.value,
            "activity_count": len(customer_activities),
            "follow_up_count": len(customer_follow_ups),
        }

    @staticmethod
    def proposal(
        intelligence_type: CRMIntelligenceType,
        customer: Customer,
        *,
        summary: str,
        rationale: str,
        confidence: float | None = None,
        proposed_action: str | None = None,
    ) -> AIProposal:
        """Wrap provider output as a non-executing CRM proposal."""
        return AIProposal(
            intelligence_type=intelligence_type,
            customer_id=customer.id,
            summary=summary,
            rationale=rationale,
            confidence=confidence,
            proposed_action=proposed_action,
        )
