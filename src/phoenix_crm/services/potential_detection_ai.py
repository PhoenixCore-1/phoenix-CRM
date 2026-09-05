"""Potential Detection AI capability for Phoenix CRM 360.

CRM owns potential/solution intelligence and proposal presentation. Phoenix
Core owns the AI provider, tenant isolation, permissions, governance, audit,
usage/cost controls, and authorization boundary.
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
class PotentialDetectionContext:
    """CRM-owned customer context selected for potential detection."""

    tenant_id: UUID
    customer_id: UUID
    values: Mapping[str, object]


class PotentialDetectionAIService:
    """Build and evaluate provider-independent potential detection requests."""

    intelligence_type = CRMIntelligenceType.POTENTIAL_DETECTION

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> PotentialDetectionContext:
        """Build authorized potential-detection context through Core."""
        context = CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=CRMIntelligenceType.POTENTIAL_DETECTION,
            values=values,
            request_context=request_context,
        )
        return PotentialDetectionContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            values=dict(context.values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: PotentialDetectionContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Evaluate potential detection through Core; never create a potential."""
        crm_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            intelligence_type=CRMIntelligenceType.POTENTIAL_DETECTION,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=crm_context,
            capability=capability,
            request_context=request_context,
        )
        if result.proposal is not None and result.proposal.intelligence_type is not CRMIntelligenceType.POTENTIAL_DETECTION:
            raise ValueError("potential detection AI capability returned the wrong intelligence type")
        if result.proposal is not None and result.proposal.customer_id != context.customer_id:
            raise ValueError("potential detection AI capability returned the wrong customer")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation state."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
