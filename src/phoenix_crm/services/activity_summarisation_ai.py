"""Activity Summarisation AI capability for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import CustomerActivity
from phoenix_crm.services.ai_intelligence import CRMIntelligenceType
from phoenix_crm.services.crm_ai_foundation import (
    AIAvailability,
    CRMAIContext,
    CRMAIResult,
    CRMAIService,
    CoreAICapability,
)


@dataclass(frozen=True, slots=True)
class ActivitySummarisationContext:
    """CRM-owned activity data selected for summarisation."""

    tenant_id: UUID
    customer_id: UUID
    values: Mapping[str, object]


class ActivitySummarisationAIService:
    """Build and evaluate provider-independent activity-summary requests."""

    intelligence_type = CRMIntelligenceType.ACTIVITY_SUMMARY

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        activities: list[CustomerActivity],
        request_context: RequestContext | None = None,
    ) -> ActivitySummarisationContext:
        """Build authorized activity context through the Core AI boundary."""
        customer_activities = [
            activity for activity in activities
            if activity.tenant_id == tenant_id and activity.customer_id == customer_id
        ]
        values = {
            "activity_count": len(customer_activities),
            "activities": tuple(
                {
                    "id": str(activity.id),
                    "activity_type": activity.activity_type.value,
                    "subject": activity.subject,
                    "occurred_at": activity.occurred_at.isoformat(),
                    "outcome": activity.outcome.value if activity.outcome is not None else None,
                    "notes": activity.notes,
                    "performed_by_user_id": str(activity.performed_by_user_id) if activity.performed_by_user_id else None,
                    "direction": activity.direction.value if activity.direction is not None else None,
                    "source": activity.source.value if activity.source is not None else None,
                }
                for activity in sorted(customer_activities, key=lambda item: (item.occurred_at, str(item.id)), reverse=True)
            ),
        }
        context = CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=CRMIntelligenceType.ACTIVITY_SUMMARY,
            values=values,
            request_context=request_context,
        )
        return ActivitySummarisationContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            values=dict(context.values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: ActivitySummarisationContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMAIResult:
        """Request an activity summary through Core AI; never modify activity data."""
        crm_context = CRMAIContext(
            tenant_id=context.tenant_id,
            customer_id=context.customer_id,
            intelligence_type=CRMIntelligenceType.ACTIVITY_SUMMARY,
            values=dict(context.values),
        )
        result = CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=crm_context,
            capability=capability,
            request_context=request_context,
        )
        if result.proposal is not None and result.proposal.intelligence_type is not CRMIntelligenceType.ACTIVITY_SUMMARY:
            raise ValueError("activity summarisation AI capability returned the wrong intelligence type")
        return result

    @staticmethod
    def unavailable() -> CRMAIResult:
        """Return the explicit graceful-degradation state."""
        return CRMAIResult(AIAvailability.UNAVAILABLE)
