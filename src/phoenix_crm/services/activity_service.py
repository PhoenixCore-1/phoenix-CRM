"""Activity services for Phoenix CRM 360."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerActivity


class ActivityService:
    """Manage CRM activities and derive chronological relationship history."""

    @staticmethod
    def record_activity(
        activity: CustomerActivity,
        customer: Customer,
    ) -> CustomerActivity:
        """Validate and record an activity against its CRM customer."""
        if activity.tenant_id != customer.tenant_id:
            raise ValueError("Activity and customer must belong to the same tenant")
        if activity.customer_id != customer.id:
            raise ValueError("Activity customer does not match the supplied customer")
        return activity

    @staticmethod
    def history_for_customer(
        customer_id: UUID,
        activities: list[CustomerActivity],
        *,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> tuple[CustomerActivity, ...]:
        """Return a customer's activities in newest-first chronological order."""
        history = [activity for activity in activities if activity.customer_id == customer_id]
        if after is not None:
            history = [activity for activity in history if activity.occurred_at >= after]
        if before is not None:
            history = [activity for activity in history if activity.occurred_at <= before]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(history)

    @staticmethod
    def history_for_contact(
        contact_id: UUID,
        activities: list[CustomerActivity],
    ) -> tuple[CustomerActivity, ...]:
        """Return activities associated with a specific contact, newest first."""
        history = [activity for activity in activities if activity.contact_id == contact_id]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(history)
