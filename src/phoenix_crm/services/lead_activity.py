"""Lead activity integration services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import CustomerActivity, Lead
from phoenix_crm.services.lead_access import LeadAccessService


@dataclass(frozen=True, slots=True)
class LeadActivityContext:
    """Presentation context linking an activity to its CRM lead."""

    activity: CustomerActivity
    lead_id: UUID
    is_converted_lead: bool


class LeadActivityService:
    """Provide lead activity history without creating a second activity model."""

    @staticmethod
    def record_activity(
        activity: CustomerActivity,
        lead: Lead,
        *,
        context: RequestContext | None = None,
    ) -> CustomerActivity:
        """Validate that an activity explicitly references the supplied lead."""
        LeadActivityService._require_access(lead, context)
        if activity.tenant_id != lead.tenant_id:
            raise ValueError("Activity and lead must belong to the same tenant")
        if activity.lead_id != lead.id:
            raise ValueError("Activity lead reference does not match the supplied lead")
        return activity

    @staticmethod
    def history_for_lead(
        lead: Lead,
        activities: list[CustomerActivity],
        *,
        before: datetime | None = None,
        after: datetime | None = None,
        context: RequestContext | None = None,
    ) -> tuple[LeadActivityContext, ...]:
        """Return a lead's activities newest first using the shared activity model."""
        LeadActivityService._require_access(lead, context)
        history = [
            activity
            for activity in activities
            if activity.tenant_id == lead.tenant_id
            and activity.lead_id == lead.id
        ]
        if after is not None:
            history = [activity for activity in history if activity.occurred_at >= after]
        if before is not None:
            history = [activity for activity in history if activity.occurred_at <= before]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(
            LeadActivityContext(
                activity=activity,
                lead_id=lead.id,
                is_converted_lead=lead.status.value == "converted",
            )
            for activity in history
        )

    @staticmethod
    def attach_lead_reference(
        activity: CustomerActivity,
        lead: Lead,
        *,
        context: RequestContext | None = None,
    ) -> None:
        """Attach the explicit CRM lead identity to an activity."""
        LeadActivityService._require_access(lead, context)
        if activity.tenant_id != lead.tenant_id:
            raise ValueError("Activity and lead must belong to the same tenant")
        if activity.customer_id is not None:
            activity.customer_id = None
        activity.lead_id = lead.id
        metadata = dict(activity.metadata)
        metadata["lead_id"] = str(lead.id)
        activity.set_communication_context(metadata=metadata)

    @staticmethod
    def _require_access(lead: Lead, context: RequestContext | None) -> None:
        if context is not None:
            LeadAccessService.require_access(lead, context)
