"""Lead AI assistance services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import CustomerActivity, CustomerFollowUp, Lead, LeadStatus
from phoenix_crm.services.lead_matching import LeadMatch, LeadMatchingService


class LeadIntelligenceType(str, Enum):
    """Supported provider-independent lead AI assistance categories."""

    QUALIFICATION_ASSISTANCE = "qualification_assistance"
    DUPLICATE_REVIEW = "duplicate_review"
    CONVERSION_READINESS = "conversion_readiness"
    NEXT_BEST_ACTION = "next_best_action"
    LEAD_SUMMARY = "lead_summary"


@dataclass(frozen=True, slots=True)
class LeadAIContext:
    """Tenant- and access-scoped context envelope for Core AI services."""

    lead_id: UUID
    tenant_id: UUID
    status: LeadStatus
    lead_name: str
    company_name: str | None
    source: str
    assigned_to_user_id: UUID | None
    activity_count: int
    follow_up_count: int
    customer_matches: tuple[LeadMatch, ...]


@dataclass(frozen=True, slots=True)
class LeadAIProposal:
    """Non-executing AI recommendation requiring authorized human approval."""

    intelligence_type: LeadIntelligenceType
    lead_id: UUID
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


class LeadAIService:
    """Prepare lead AI context and proposals without calling an AI provider."""

    @staticmethod
    def context_for_lead(
        lead: Lead,
        *,
        activities: list[CustomerActivity] | tuple[CustomerActivity, ...] = (),
        follow_ups: list[CustomerFollowUp] | tuple[CustomerFollowUp, ...] = (),
        customers=(),
        context: RequestContext | None = None,
    ) -> LeadAIContext:
        """Build deterministic, scoped context for Core AI processing."""
        LeadAIService._require_access(lead, context)
        scoped_activities = tuple(
            activity for activity in activities
            if activity.tenant_id == lead.tenant_id
            and activity.metadata.get("lead_id") == str(lead.id)
        )
        scoped_follow_ups = tuple(
            follow_up for follow_up in follow_ups
            if follow_up.tenant_id == lead.tenant_id
        )
        matches = tuple(LeadMatchingService.customer_matches(lead, customers))
        return LeadAIContext(
            lead_id=lead.id,
            tenant_id=lead.tenant_id,
            status=lead.status,
            lead_name=lead.name,
            company_name=lead.company_name,
            source=lead.source.value,
            assigned_to_user_id=lead.assigned_to_user_id,
            activity_count=len(scoped_activities),
            follow_up_count=len(scoped_follow_ups),
            customer_matches=matches,
        )

    @staticmethod
    def proposal(
        intelligence_type: LeadIntelligenceType,
        lead: Lead,
        *,
        summary: str,
        rationale: str,
        confidence: float | None = None,
        proposed_action: str | None = None,
        context: RequestContext | None = None,
    ) -> LeadAIProposal:
        """Create a non-executing proposal for an authorized lead."""
        LeadAIService._require_access(lead, context)
        return LeadAIProposal(
            intelligence_type=intelligence_type,
            lead_id=lead.id,
            summary=summary,
            rationale=rationale,
            confidence=confidence,
            proposed_action=proposed_action,
        )

    @staticmethod
    def _require_access(lead: Lead, context: RequestContext | None) -> None:
        if context is None:
            return
        if context.tenant.tenant_id != str(lead.tenant_id):
            raise PermissionError("Core access scope tenant does not match lead")
        if not context.can_access_resource(str(lead.id)):
            raise PermissionError("Core access scope does not include this lead")
