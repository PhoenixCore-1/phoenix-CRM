"""Call cadence services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerActivity, CustomerCallClass


@dataclass(frozen=True, slots=True)
class CadenceResult:
    """Resolved customer contact cadence and next planned interaction."""

    customer_id: UUID
    call_class_id: UUID
    interval_days: int | None
    last_interaction_at: datetime | None
    next_interaction_at: datetime | None


class CallCadenceService:
    """Calculate contact cadence without creating follow-ups or work queues."""

    @staticmethod
    def resolve(
        customer: Customer,
        call_class: CustomerCallClass,
        activities: list[CustomerActivity],
        *,
        reference_at: datetime | None = None,
    ) -> CadenceResult:
        """Resolve cadence from the customer's configured call class."""
        if call_class.id != customer.call_class_id:
            raise ValueError("Call class does not match the customer")

        customer_activities = [
            activity
            for activity in activities
            if activity.tenant_id == customer.tenant_id
            and activity.customer_id == customer.id
        ]
        customer_activities.sort(
            key=lambda activity: (activity.occurred_at, str(activity.id)),
            reverse=True,
        )
        last_interaction_at = (
            customer_activities[0].occurred_at if customer_activities else None
        )
        next_interaction_at = CallCadenceService.next_interaction_at(
            last_interaction_at,
            call_class,
            reference_at=reference_at,
        )
        return CadenceResult(
            customer_id=customer.id,
            call_class_id=call_class.id,
            interval_days=call_class.cadence.interval_days,
            last_interaction_at=last_interaction_at,
            next_interaction_at=next_interaction_at,
        )

    @staticmethod
    def next_interaction_at(
        last_interaction_at: datetime | None,
        call_class: CustomerCallClass,
        *,
        reference_at: datetime | None = None,
    ) -> datetime | None:
        """Calculate the next contact date from the configured interval.

        If no interaction exists, the reference time is used as the cadence
        anchor. A class with no configured interval produces no planned date.
        """
        interval_days = call_class.cadence.interval_days
        if interval_days is None:
            return None

        anchor = last_interaction_at or reference_at or datetime.now(timezone.utc)
        return anchor + timedelta(days=interval_days)

    @staticmethod
    def last_interaction(
        customer_id: UUID,
        activities: list[CustomerActivity],
        *,
        tenant_id: UUID | None = None,
    ) -> datetime | None:
        """Return the newest activity timestamp for a customer.

        When tenant_id is supplied, activities from other tenants are ignored.
        Supplying tenant_id is recommended for multi-tenant callers.
        """
        matching = [
            activity
            for activity in activities
            if activity.customer_id == customer_id
            and (tenant_id is None or activity.tenant_id == tenant_id)
        ]
        if not matching:
            return None
        return max(activity.occurred_at for activity in matching)
