"""CRM call and follow-up work queue for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Customer, CustomerActivity, CustomerCallClass, CustomerFollowUp, FollowUpStatus
from phoenix_crm.services.call_cadence import CallCadenceService


class CRMWorkItemType(str, Enum):
    """Action types represented by the CRM relationship work queue."""

    CALL = "call"
    FOLLOW_UP = "follow_up"


@dataclass(frozen=True, slots=True)
class CRMWorkQueueItem:
    """Immutable, presentation-ready CRM relationship work item."""

    customer_id: UUID
    customer_name: str
    item_type: CRMWorkItemType
    due_at: datetime
    follow_up_id: UUID | None = None
    assigned_to_user_id: UUID | None = None


class CustomerCallFollowUpQueueService:
    """Build the actionable CRM call/follow-up queue from CRM-owned data."""

    ACTIVE_FOLLOW_UP_STATUSES = frozenset({FollowUpStatus.PLANNED, FollowUpStatus.DUE})

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customers: tuple[Customer, ...] | list[Customer] = (),
        activities: tuple[CustomerActivity, ...] | list[CustomerActivity] = (),
        follow_ups: tuple[CustomerFollowUp, ...] | list[CustomerFollowUp] = (),
        call_classes: tuple[CustomerCallClass, ...] | list[CustomerCallClass] = (),
        reference_at: datetime,
        request_context: RequestContext | None = None,
    ) -> tuple[CRMWorkQueueItem, ...]:
        """Build a deterministic queue containing cadence calls and open follow-ups."""
        CustomerCallFollowUpQueueService._require_access(tenant_id, request_context)

        scoped_customers = tuple(
            customer
            for customer in customers
            if customer.tenant_id == tenant_id
            and CustomerCallFollowUpQueueService._accessible(customer.id, request_context)
        )
        customer_ids = {customer.id for customer in scoped_customers}
        scoped_activities = tuple(
            activity
            for activity in activities
            if activity.tenant_id == tenant_id and activity.customer_id in customer_ids
        )
        scoped_follow_ups = tuple(
            follow_up
            for follow_up in follow_ups
            if follow_up.tenant_id == tenant_id
            and follow_up.customer_id in customer_ids
            and follow_up.status in CustomerCallFollowUpQueueService.ACTIVE_FOLLOW_UP_STATUSES
        )
        classes = {call_class.id: call_class for call_class in call_classes}
        items: list[CRMWorkQueueItem] = []

        for customer in scoped_customers:
            call_class = classes.get(customer.call_class_id)
            if call_class is not None:
                cadence = CallCadenceService.resolve(
                    customer,
                    call_class,
                    list(scoped_activities),
                    reference_at=reference_at,
                )
                if cadence.next_interaction_at is not None:
                    items.append(
                        CRMWorkQueueItem(
                            customer_id=customer.id,
                            customer_name=customer.name,
                            item_type=CRMWorkItemType.CALL,
                            due_at=cadence.next_interaction_at,
                            assigned_to_user_id=customer.account_owner_id,
                        )
                    )

        for follow_up in scoped_follow_ups:
            customer = next((item for item in scoped_customers if item.id == follow_up.customer_id), None)
            if customer is None:
                continue
            items.append(
                CRMWorkQueueItem(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_type=CRMWorkItemType.FOLLOW_UP,
                    due_at=follow_up.due_at,
                    follow_up_id=follow_up.id,
                    assigned_to_user_id=follow_up.assigned_to_user_id,
                )
            )

        # Calls are the primary relationship-planning item; follow-ups are the
        # secondary action queue. Keep that precedence deterministic, then sort
        # by due time within each item type.
        item_type_order = {
            CRMWorkItemType.CALL: 0,
            CRMWorkItemType.FOLLOW_UP: 1,
        }
        items.sort(
            key=lambda item: (
                item_type_order[item.item_type],
                item.due_at,
                str(item.customer_id),
                str(item.follow_up_id or ""),
            )
        )
        return tuple(items)

    @staticmethod
    def for_user(
        items: tuple[CRMWorkQueueItem, ...],
        user_id: UUID,
    ) -> tuple[CRMWorkQueueItem, ...]:
        """Return assigned work while preserving deterministic queue order."""
        return tuple(item for item in items if item.assigned_to_user_id == user_id)

    @staticmethod
    def overdue(
        items: tuple[CRMWorkQueueItem, ...],
        *,
        reference_at: datetime,
    ) -> tuple[CRMWorkQueueItem, ...]:
        """Return overdue work items while preserving queue order."""
        return tuple(item for item in items if item.due_at < reference_at)

    @staticmethod
    def due_or_overdue(
        items: tuple[CRMWorkQueueItem, ...],
        *,
        reference_at: datetime,
    ) -> tuple[CRMWorkQueueItem, ...]:
        """Return all work due at or before the reference time."""
        return tuple(item for item in items if item.due_at <= reference_at)

    @staticmethod
    def _accessible(resource_id: UUID, request_context: RequestContext | None) -> bool:
        return request_context is None or request_context.can_access_resource(str(resource_id))

    @staticmethod
    def _require_access(tenant_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is not None and request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this tenant")
