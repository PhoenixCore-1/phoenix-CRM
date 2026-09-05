"""Customer potential application service for Phoenix CRM 360."""

from __future__ import annotations

from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import CustomerPotential, PotentialPriority, PotentialSource
from phoenix_crm.services.lead_access import LeadAccessService


class CustomerPotentialService:
    """Create and retrieve customer potentials within CRM boundaries."""

    @staticmethod
    def create(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        solution_name: str,
        reason: str,
        source: PotentialSource,
        priority: PotentialPriority = PotentialPriority.NORMAL,
        context: str | None = None,
        current_solution: str | None = None,
        assigned_to_user_id: UUID | None = None,
        request_context: RequestContext | None = None,
    ) -> CustomerPotential:
        """Create a CRM-owned potential after validating Core scope."""
        CustomerPotentialService._require_customer_scope(customer_id, tenant_id, request_context)
        return CustomerPotential(
            tenant_id=tenant_id,
            customer_id=customer_id,
            solution_name=solution_name,
            reason=reason,
            source=source,
            priority=priority,
            context=context,
            current_solution=current_solution,
            assigned_to_user_id=assigned_to_user_id,
        )

    @staticmethod
    def for_customer(
        customer_id: UUID,
        potentials: list[CustomerPotential] | tuple[CustomerPotential, ...],
        *,
        tenant_id: UUID | None = None,
        request_context: RequestContext | None = None,
    ) -> tuple[CustomerPotential, ...]:
        """Return customer potentials constrained by tenant and Core scope."""
        items = [item for item in potentials if item.customer_id == customer_id]
        if tenant_id is not None:
            items = [item for item in items if item.tenant_id == tenant_id]
        if request_context is not None:
            items = [
                item for item in items
                if item.tenant_id.__str__() == request_context.tenant.tenant_id
                and request_context.can_access_resource(str(item.customer_id))
            ]
        items.sort(key=lambda item: (item.priority.value, item.updated_at, str(item.id)), reverse=True)
        return tuple(items)

    @staticmethod
    def _require_customer_scope(
        customer_id: UUID,
        tenant_id: UUID,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
