"""Lead Qualification Assistance AI for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.ai_intelligence import AIProposal, CRMIntelligenceType
from phoenix_crm.services.crm_ai_foundation import (
    AIAvailability,
    CRMAIContext,
    CRMAIResult,
    CRMAIService,
    CoreAICapability,
)


@dataclass(frozen=True, slots=True)
class LeadQualificationAIContext:
    """CRM-owned lead signals supplied to Core AI for qualification assistance."""

    tenant_id: UUID
    lead_id: UUID
    values: Mapping[str, object]


class LeadQualificationAIService:
    """Provide non-executing AI assistance for lead qualification."""

    intelligence_type = CRMIntelligenceType.LEAD_QUALIFICATION

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        lead_id: UUID,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> LeadQualificationAIContext:
        """Build tenant/access-scoped lead qualification context."""
        if request_context is not None:
            if request_context.tenant.tenant_id != str(tenant_id):
                raise ValueError("request context tenant does not match lead qualification tenant")
            if not request_context.can_access_resource(str(lead_id)):
                raise PermissionError("lead is outside the request access scope")
        return LeadQualificationAIContext(
            tenant_id=tenant_id,
            lead_id=lead_id,
            values=dict(values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: LeadQualificationAIContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Evaluate lead qualification assistance; never qualify or convert."""
        if request_context is not None:
            if request_context.tenant.tenant_id != str(tenant_id):
                raise ValueError("request context tenant does not match lead qualification tenant")
            if request_context.user.user_id != str(user_id):
                raise PermissionError("request user does not match lead qualification user")
            if not request_context.can_access_resource(str(context.lead_id)):
                raise PermissionError("lead is outside the request access scope")

        ai_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.lead_id,
            intelligence_type=CRMIntelligenceType.LEAD_QUALIFICATION,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=ai_context,
            capability=capability,
            request_context=None,
        )
        if result.proposal is not None:
            if result.proposal.intelligence_type is not CRMIntelligenceType.LEAD_QUALIFICATION:
                raise ValueError("lead qualification AI capability returned the wrong intelligence type")
            if result.proposal.customer_id != context.lead_id:
                raise ValueError("lead qualification AI capability returned the wrong resource")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return explicit graceful degradation when Core AI is unavailable."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
