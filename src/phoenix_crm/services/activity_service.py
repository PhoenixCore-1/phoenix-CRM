"""Activity services for Phoenix CRM 360."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
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
        tenant_id: UUID | None = None,
        request_context: RequestContext | None = None,
    ) -> tuple[CustomerActivity, ...]:
        """Return a customer's activities in newest-first chronological order."""
        ActivityService._validate_history_scope(customer_id, tenant_id, request_context)
        history = [
            activity
            for activity in activities
            if activity.customer_id == customer_id
            and (tenant_id is None or activity.tenant_id == tenant_id)
        ]
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
        *,
        tenant_id: UUID | None = None,
        request_context: RequestContext | None = None,
    ) -> tuple[CustomerActivity, ...]:
        """Return activities associated with a specific contact, newest first."""
        ActivityService._validate_history_scope(contact_id, tenant_id, request_context)
        history = [
            activity
            for activity in activities
            if activity.contact_id == contact_id
            and (tenant_id is None or activity.tenant_id == tenant_id)
        ]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(history)

    @staticmethod
    def _validate_history_scope(
        resource_id: UUID,
        tenant_id: UUID | None,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        context_tenant_id = request_context.tenant.tenant_id
        if tenant_id is not None and str(tenant_id) != context_tenant_id:
            raise PermissionError("Core access scope does not include this tenant")
        if not request_context.can_access_resource(str(resource_id)):
            raise PermissionError("Core access scope does not include this resource")
