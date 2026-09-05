"""Customer call preparation AI capability for Phoenix CRM 360.

CRM owns the call-preparation use case. Phoenix Core owns the AI provider,
security, governance, and authorization boundary.
"""

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
class CallPreparationContext:
    """CRM-owned context selected for preparing a customer interaction."""

    tenant_id: UUID
    customer_id: UUID
    values: Mapping[str, object]


class CallPreparationAIService:
    """Build and evaluate provider-independent call-preparation requests."""

    intelligence_type = CRMIntelligenceType.CALL_PREPARATION

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> CallPreparationContext:
        """Build call-preparation context through the Core AI access boundary."""
        context = CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=CRMIntelligenceType.CALL_PREPARATION,
            values=values,
            request_context=request_context,
        )
        return CallPreparationContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            values=dict(context.values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: CallPreparationContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Evaluate call preparation through Core; unavailable degrades safely."""
        crm_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            intelligence_type=CRMIntelligenceType.CALL_PREPARATION,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=crm_context,
            capability=capability,
            request_context=request_context,
        )
        if result.proposal is not None and result.proposal.intelligence_type is not CRMIntelligenceType.CALL_PREPARATION:
            raise ValueError("call preparation AI capability returned the wrong intelligence type")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation state."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
