"""Next Best Action AI capability for Phoenix CRM 360.

CRM owns the relationship-management use case. Phoenix Core owns the AI
provider, tenant isolation, permissions, governance, audit, usage/cost
controls, and authorization boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.ai_intelligence import CRMIntelligenceType
from phoenix_crm.services.crm_ai_foundation import (
    AIAvailability,
    CRMAIContext,
    CRMAIResult,
    CRMAIService,
    CoreAICapability,
)


@dataclass(frozen=True, slots=True)
class NextBestActionContext:
    """CRM-owned relationship context selected for next-action guidance."""

    tenant_id: UUID
    customer_id: UUID
    values: Mapping[str, object]


class NextBestActionAIService:
    """Build and evaluate provider-independent next-action requests."""

    intelligence_type = CRMIntelligenceType.NEXT_BEST_ACTION

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> NextBestActionContext:
        """Build authorized next-action context through the Core boundary."""
        context = CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
            values=values,
            request_context=request_context,
        )
        return NextBestActionContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            values=dict(context.values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: NextBestActionContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Evaluate next-action guidance through Core; never execute an action."""
        crm_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=crm_context,
            capability=capability,
            request_context=request_context,
        )
        if result.proposal is not None and result.proposal.intelligence_type is not CRMIntelligenceType.NEXT_BEST_ACTION:
            raise ValueError("next best action AI capability returned the wrong intelligence type")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation state."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
