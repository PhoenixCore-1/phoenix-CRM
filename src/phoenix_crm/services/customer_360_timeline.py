"""Customer 360 relationship timeline for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import CustomerActivity
from phoenix_crm.services.activity_service import ActivityService


@dataclass(frozen=True, slots=True)
class Customer360TimelineEntry:
    """Read-only timeline entry derived from an existing CRM activity."""

    activity_id: UUID
    customer_id: UUID
    activity_type: str
    subject: str
    occurred_at: datetime
    contact_id: UUID | None
    performed_by_user_id: UUID | None
    outcome: str | None
    notes: str | None
    direction: str
    source: str
    duration_minutes: int | None
    communication_reference: str | None


@dataclass(frozen=True, slots=True)
class Customer360Timeline:
    """Read-only chronological relationship history for Customer 360."""

    tenant_id: UUID
    customer_id: UUID
    entries: tuple[Customer360TimelineEntry, ...]


class Customer360TimelineService:
    """Compose Customer 360 timeline data without owning activities."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        activities: list[CustomerActivity] | tuple[CustomerActivity, ...] = (),
        request_context: RequestContext | None = None,
        limit: int | None = None,
    ) -> Customer360Timeline:
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive when supplied")
        Customer360TimelineService._require_access(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )
        customer_activities = tuple(
            activity
            for activity in activities
            if activity.tenant_id == tenant_id and activity.customer_id == customer_id
        )
        history = ActivityService.history_for_customer(customer_id, list(customer_activities))
        if limit is not None:
            history = history[:limit]
        entries = tuple(Customer360TimelineService._entry(activity) for activity in history)
        return Customer360Timeline(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entries=entries,
        )

    @staticmethod
    def _entry(activity: CustomerActivity) -> Customer360TimelineEntry:
        return Customer360TimelineEntry(
            activity_id=activity.id,
            customer_id=activity.customer_id,
            activity_type=activity.activity_type.value,
            subject=activity.subject,
            occurred_at=activity.occurred_at,
            contact_id=activity.contact_id,
            performed_by_user_id=activity.performed_by_user_id,
            outcome=activity.outcome.value if activity.outcome is not None else None,
            notes=activity.notes,
            direction=activity.direction.value,
            source=activity.source.value,
            duration_minutes=activity.duration_minutes,
            communication_reference=activity.communication_reference,
        )

    @staticmethod
    def _require_access(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
