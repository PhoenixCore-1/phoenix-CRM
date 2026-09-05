"""Customer Summary AI capability for Phoenix CRM 360."""

from __future__ import annotations

from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Customer, CustomerActivity, CustomerFollowUp
from phoenix_crm.services.ai_intelligence import CRMIntelligenceService, CRMIntelligenceType
from phoenix_crm.services.crm_ai_foundation import (
    AIAvailability,
    CRMAIResult,
    CRMAIService,
    CoreAICapability,
)


class CustomerSummaryAIService:
    """Prepare customer-summary context and evaluate it through Core AI."""

    @staticmethod
    def build_context(
        customer: Customer,
        activities: list[CustomerActivity],
        follow_ups: list[CustomerFollowUp],
        *,
        request_context: RequestContext | None = None,
    ):
        """Build the authorized CRM context used for a customer summary."""
        values = CRMIntelligenceService.context_for_customer(customer, activities, follow_ups)
        return CRMAIService.build_context(
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
            values=values,
            request_context=request_context,
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Request a customer summary from Core AI; never execute an action."""
        if context.intelligence_type is not CRMIntelligenceType.CUSTOMER_SUMMARY:
            raise ValueError("Customer Summary AI requires customer_summary intelligence type")
        return CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=context,
            capability=capability,
            request_context=request_context,
        )

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation result."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
