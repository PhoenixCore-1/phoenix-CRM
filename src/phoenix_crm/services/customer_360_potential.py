"""Customer 360 potential and solution presentation for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import (
    CustomerPotential,
    CustomerSolution,
    PotentialPriority,
    PotentialStatus,
    SolutionRelationship,
    SolutionStatus,
)
from phoenix_crm.services.potential_service import CustomerPotentialService


@dataclass(frozen=True, slots=True)
class Customer360PotentialItem:
    """Read-only potential item for Customer 360."""

    potential_id: UUID
    solution_name: str
    status: PotentialStatus
    priority: PotentialPriority
    reason: str
    context: str | None
    current_solution: str | None
    assigned_to_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class Customer360SolutionItem:
    """Read-only current/potential solution relationship for Customer 360."""

    solution_id: UUID
    solution_name: str
    relationship: SolutionRelationship
    reason: str | None
    source: str | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class Customer360PotentialSection:
    """Read-only potential/opportunity section for Customer 360.

    CRM owns relationship potential and solution intelligence. This section
    deliberately does not represent Sales opportunities, quotes, pricing or
    orders; those remain external contract references owned by their module.
    """

    tenant_id: UUID
    customer_id: UUID
    active_potential_count: int
    qualified_potential_count: int
    high_priority_potential_count: int
    potentials: tuple[Customer360PotentialItem, ...]
    current_solutions: tuple[Customer360SolutionItem, ...]
    potential_solutions: tuple[Customer360SolutionItem, ...]


class Customer360PotentialService:
    """Compose CRM-owned potential data for Customer 360."""

    ACTIVE_POTENTIAL_STATUSES = frozenset({
        PotentialStatus.IDENTIFIED,
        PotentialStatus.QUALIFYING,
        PotentialStatus.QUALIFIED,
    })

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        potentials: list[CustomerPotential] | tuple[CustomerPotential, ...] = (),
        solutions: list[CustomerSolution] | tuple[CustomerSolution, ...] = (),
        request_context: RequestContext | None = None,
    ) -> Customer360PotentialSection:
        Customer360PotentialService._require_access(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )

        customer_potentials = CustomerPotentialService.for_customer(
            customer_id,
            potentials,
            tenant_id=tenant_id,
            request_context=request_context,
        )
        customer_potentials = tuple(
            item for item in customer_potentials
            if item.status in Customer360PotentialService.ACTIVE_POTENTIAL_STATUSES
        )

        customer_solutions = tuple(
            item for item in solutions
            if item.tenant_id == tenant_id
            and item.customer_id == customer_id
            and item.status == SolutionStatus.ACTIVE
        )
        current = tuple(
            Customer360PotentialService._solution_item(item)
            for item in customer_solutions
            if item.relationship is SolutionRelationship.CURRENT
        )
        potential = tuple(
            Customer360PotentialService._solution_item(item)
            for item in customer_solutions
            if item.relationship is SolutionRelationship.POTENTIAL
        )

        items = tuple(Customer360PotentialService._potential_item(item) for item in customer_potentials)
        return Customer360PotentialSection(
            tenant_id=tenant_id,
            customer_id=customer_id,
            active_potential_count=len(items),
            qualified_potential_count=sum(item.status is PotentialStatus.QUALIFIED for item in customer_potentials),
            high_priority_potential_count=sum(item.priority in {PotentialPriority.HIGH, PotentialPriority.URGENT} for item in customer_potentials),
            potentials=items,
            current_solutions=current,
            potential_solutions=potential,
        )

    @staticmethod
    def _potential_item(item: CustomerPotential) -> Customer360PotentialItem:
        return Customer360PotentialItem(
            potential_id=item.id,
            solution_name=item.solution_name,
            status=item.status,
            priority=item.priority,
            reason=item.reason,
            context=item.context,
            current_solution=item.current_solution,
            assigned_to_user_id=item.assigned_to_user_id,
        )

    @staticmethod
    def _solution_item(item: CustomerSolution) -> Customer360SolutionItem:
        return Customer360SolutionItem(
            solution_id=item.id,
            solution_name=item.solution_name,
            relationship=item.relationship,
            reason=item.reason,
            source=item.source,
            notes=item.notes,
        )

    @staticmethod
    def _require_access(*, tenant_id: UUID, customer_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
