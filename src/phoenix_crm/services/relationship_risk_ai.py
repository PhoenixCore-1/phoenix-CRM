"""Relationship Risk AI capability for Phoenix CRM 360.

CRM owns relationship intelligence. Phoenix Core owns the AI provider,
tenant isolation, permissions, governance, audit, usage/cost controls, and
authorization boundary.
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
class RelationshipRiskContext:
    """CRM-owned relationship signals selected for risk assessment."""

    tenant_id: UUID
    customer_id: UUID
    values: Mapping[str, object]


class RelationshipRiskAIService:
    """Build and evaluate provider-independent relationship-risk requests."""

    intelligence_type = CRMIntelligenceType.RELATIONSHIP_RISK

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> RelationshipRiskContext:
        """Build authorized relationship-risk context through Core."""
        context = CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=CRMIntelligenceType.RELATIONSHIP_RISK,
            values=values,
            request_context=request_context,
        )
        return RelationshipRiskContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            values=dict(context.values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: RelationshipRiskContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Evaluate relationship risk through Core; never change CRM state."""
        crm_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            intelligence_type=CRMIntelligenceType.RELATIONSHIP_RISK,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=crm_context,
            capability=capability,
            request_context=request_context,
        )
        if result.proposal is not None and result.proposal.intelligence_type is not CRMIntelligenceType.RELATIONSHIP_RISK:
            raise ValueError("relationship risk AI capability returned the wrong intelligence type")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation state."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
