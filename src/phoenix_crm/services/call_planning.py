"""Call planning and work-queue foundation for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerActivity, CustomerFollowUp
from phoenix_crm.services.call_cadence import CallCadenceService


class CallPlanItemType(str, Enum):
    """Reason a customer appears in the call-planning queue."""

    CADENCE = "cadence"
    FOLLOW_UP = "follow_up"


@dataclass(frozen=True, slots=True)
class CallPlanItem:
    """Presentation-ready customer action for the CRM call plan."""

    customer_id: UUID
    customer_name: str
    item_type: CallPlanItemType
    due_at: datetime
    follow_up_id: UUID | None = None


class CallPlanningService:
    """Build a deterministic call-planning queue without owning scheduling policy."""

    @staticmethod
    def build(
        customers: list[Customer],
        call_classes: dict[UUID, object],
        activities: list[CustomerActivity],
        follow_ups: list[CustomerFollowUp],
        *,
        reference_at: datetime,
    ) -> tuple[CallPlanItem, ...]:
        """Build customer cadence and follow-up items for planning.

        This foundation only assembles actionable items. Temporal overdue and
        upcoming classification remains a later phase.
        """
        items: list[CallPlanItem] = []
        for customer in customers:
            call_class = call_classes.get(customer.call_class_id)
            if call_class is not None:
                cadence = CallCadenceService.resolve(
                    customer,
                    call_class,
                    activities,
                    reference_at=reference_at,
                )
                if cadence.next_interaction_at is not None:
                    items.append(
                        CallPlanItem(
                            customer_id=customer.id,
                            customer_name=customer.name,
                            item_type=CallPlanItemType.CADENCE,
                            due_at=cadence.next_interaction_at,
                        )
                    )

            for follow_up in follow_ups:
                if follow_up.customer_id != customer.id:
                    continue
                items.append(
                    CallPlanItem(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_type=CallPlanItemType.FOLLOW_UP,
                        due_at=follow_up.due_at,
                        follow_up_id=follow_up.id,
                    )
                )

        items.sort(key=lambda item: (item.due_at, str(item.customer_id), item.item_type.value, str(item.follow_up_id or "")))
        return tuple(items)

    @staticmethod
    def for_customer(
        customer_id: UUID,
        items: tuple[CallPlanItem, ...],
    ) -> tuple[CallPlanItem, ...]:
        """Return planning items for one customer in queue order."""
        return tuple(item for item in items if item.customer_id == customer_id)
