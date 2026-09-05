"""Customer 360 overview composition for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import (
    Customer,
    CustomerActivity,
    CustomerFollowUp,
    CustomerPotential,
    CustomerSolution,
    FollowUpStatus,
    PotentialStatus,
    SolutionRelationship,
    SolutionStatus,
)
from phoenix_crm.services.customer_360_contract import Customer360View
from phoenix_crm.services.activity_service import ActivityService


@dataclass(frozen=True, slots=True)
class Customer360Overview:
    """Read-only relationship overview for one CRM customer."""

    view: Customer360View
    activity_count: int
    open_follow_up_count: int
    overdue_follow_up_count: int
    active_potential_count: int
    current_solution_count: int
    potential_solution_count: int
    last_activity_at: datetime | None


class Customer360OverviewService:
    """Compose CRM-owned overview data without creating a second aggregate."""

    OPEN_FOLLOW_UP_STATUSES = frozenset({
        FollowUpStatus.PLANNED,
        FollowUpStatus.DUE,
    })

    ACTIVE_POTENTIAL_STATUSES = frozenset({
        PotentialStatus.IDENTIFIED,
        PotentialStatus.QUALIFYING,
        PotentialStatus.QUALIFIED,
    })

    @staticmethod
    def build(
        *,
        customer: Customer,
        view: Customer360View,
        activities: list[CustomerActivity] | tuple[CustomerActivity, ...] = (),
        follow_ups: list[CustomerFollowUp] | tuple[CustomerFollowUp, ...] = (),
        potentials: list[CustomerPotential] | tuple[CustomerPotential, ...] = (),
        solutions: list[CustomerSolution] | tuple[CustomerSolution, ...] = (),
        request_context: RequestContext | None = None,
    ) -> Customer360Overview:
        """Build an overview from existing CRM domain data.

        The service is read-only. It filters supplied records by the requested
        customer and tenant and uses Core-resolved access scope when supplied.
        """
        if customer.tenant_id != view.tenant_id or customer.id != view.customer_id:
            raise ValueError("Customer and Customer 360 view do not match")
        Customer360OverviewService._require_access(customer, request_context)

        customer_activities = [
            item for item in activities
            if item.tenant_id == customer.tenant_id and item.customer_id == customer.id
        ]
        history = ActivityService.history_for_customer(customer.id, customer_activities)

        customer_follow_ups = [
            item for item in follow_ups
            if item.tenant_id == customer.tenant_id and item.customer_id == customer.id
        ]
        open_follow_ups = [
            item for item in customer_follow_ups
            if item.status in Customer360OverviewService.OPEN_FOLLOW_UP_STATUSES
        ]
        overdue_follow_ups = [
            item for item in open_follow_ups
            if item.due_at < datetime.now(item.due_at.tzinfo)
        ]

        customer_potentials = [
            item for item in potentials
            if item.tenant_id == customer.tenant_id
            and item.customer_id == customer.id
            and item.status in Customer360OverviewService.ACTIVE_POTENTIAL_STATUSES
        ]

        customer_solutions = [
            item for item in solutions
            if item.tenant_id == customer.tenant_id
            and item.customer_id == customer.id
            and item.status == SolutionStatus.ACTIVE
        ]

        return Customer360Overview(
            view=view,
            activity_count=len(history),
            open_follow_up_count=len(open_follow_ups),
            overdue_follow_up_count=len(overdue_follow_ups),
            active_potential_count=len(customer_potentials),
            current_solution_count=sum(
                item.relationship == SolutionRelationship.CURRENT
                for item in customer_solutions
            ),
            potential_solution_count=sum(
                item.relationship == SolutionRelationship.POTENTIAL
                for item in customer_solutions
            ),
            last_activity_at=history[0].occurred_at if history else None,
        )

    @staticmethod
    def _require_access(
        customer: Customer,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(customer.tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer.id)):
            raise PermissionError("Core access scope does not include this customer")
