"""Lead activity integration services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.domain import CustomerActivity, Lead


@dataclass(frozen=True, slots=True)
class LeadActivityContext:
    """Presentation context linking an activity to its CRM lead."""

    activity: CustomerActivity
    lead_id: UUID
    is_converted_lead: bool


class LeadActivityService:
    """Provide lead activity history without creating a second activity model."""

    @staticmethod
    def record_activity(activity: CustomerActivity, lead: Lead) -> CustomerActivity:
        """Validate that a lead activity carries the lead reference."""
        if activity.tenant_id != lead.tenant_id:
            raise ValueError("Activity and lead must belong to the same tenant")
        if activity.metadata.get("lead_id") != str(lead.id):
            raise ValueError("Activity lead reference does not match the supplied lead")
        return activity

    @staticmethod
    def history_for_lead(
        lead: Lead,
        activities: list[CustomerActivity],
        *,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> tuple[LeadActivityContext, ...]:
        """Return a lead's activities newest first using the shared activity model."""
        lead_id = str(lead.id)
        history = [
            activity for activity in activities
            if activity.tenant_id == lead.tenant_id
            and activity.metadata.get("lead_id") == lead_id
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
    def attach_lead_reference(activity: CustomerActivity, lead: Lead) -> None:
        """Attach the CRM lead identity without introducing a lead foreign-key field."""
        if activity.tenant_id != lead.tenant_id:
            raise ValueError("Activity and lead must belong to the same tenant")
        metadata = dict(activity.metadata)
        metadata["lead_id"] = str(lead.id)
        activity.set_communication_context(metadata=metadata)
