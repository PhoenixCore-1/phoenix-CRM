"""Follow-up application services for Phoenix CRM 360."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Customer, CustomerFollowUp, FollowUpStatus


class FollowUpService:
    """Manage follow-up lifecycle and Core-scoped retrieval."""

    @staticmethod
    def record_follow_up(
        follow_up: CustomerFollowUp,
        customer: Customer,
        *,
        context: RequestContext | None = None,
    ) -> CustomerFollowUp:
        """Validate and record a follow-up against its CRM customer."""
        FollowUpService._validate_customer(follow_up, customer)
        FollowUpService._require_access(follow_up, customer, context)
        return follow_up

    @staticmethod
    def complete(
        follow_up: CustomerFollowUp,
        customer: Customer,
        *,
        completed_at: datetime | None = None,
        context: RequestContext | None = None,
    ) -> CustomerFollowUp:
        """Complete a follow-up after validating Core access."""
        FollowUpService._validate_customer(follow_up, customer)
        FollowUpService._require_access(follow_up, customer, context)
        follow_up.complete(completed_at=completed_at)
        return follow_up

    @staticmethod
    def cancel(
        follow_up: CustomerFollowUp,
        customer: Customer,
        *,
        context: RequestContext | None = None,
    ) -> CustomerFollowUp:
        """Cancel a follow-up after validating Core access."""
        FollowUpService._validate_customer(follow_up, customer)
        FollowUpService._require_access(follow_up, customer, context)
        follow_up.cancel()
        return follow_up

    @staticmethod
    def reschedule(
        follow_up: CustomerFollowUp,
        customer: Customer,
        due_at: datetime,
        *,
        context: RequestContext | None = None,
    ) -> CustomerFollowUp:
        """Reschedule a follow-up after validating Core access."""
        FollowUpService._validate_customer(follow_up, customer)
        FollowUpService._require_access(follow_up, customer, context)
        follow_up.reschedule(due_at)
        return follow_up

    @staticmethod
    def mark_due(
        follow_up: CustomerFollowUp,
        customer: Customer,
        *,
        context: RequestContext | None = None,
    ) -> CustomerFollowUp:
        """Mark an active follow-up as due after validating Core access."""
        FollowUpService._validate_customer(follow_up, customer)
        FollowUpService._require_access(follow_up, customer, context)
        follow_up.mark_due()
        return follow_up

    @staticmethod
    def can_access(
        follow_up: CustomerFollowUp,
        customer: Customer,
        context: RequestContext,
    ) -> bool:
        """Return whether Core has granted access to the follow-up's customer."""
        FollowUpService._validate_customer(follow_up, customer)
        return (
            context.tenant.tenant_id == str(customer.tenant_id)
            and context.can_access_resource(str(customer.id))
        )

    @staticmethod
    def require_access(
        follow_up: CustomerFollowUp,
        customer: Customer,
        context: RequestContext,
    ) -> None:
        """Raise PermissionError when Core scope does not include the customer."""
        if not FollowUpService.can_access(follow_up, customer, context):
            raise PermissionError("Core access scope does not include this customer")

    @staticmethod
    def for_customer(
        customer_id: UUID,
        follow_ups: list[CustomerFollowUp],
        *,
        tenant_id: UUID | None = None,
        context: RequestContext | None = None,
    ) -> tuple[CustomerFollowUp, ...]:
        """Return a customer's follow-ups, optionally constrained by Core scope."""
        items = [follow_up for follow_up in follow_ups if follow_up.customer_id == customer_id]
        if tenant_id is not None:
            items = [item for item in items if item.tenant_id == tenant_id]
        if context is not None:
            if not context.can_access_resource(str(customer_id)):
                return ()
            items = [item for item in items if str(item.tenant_id) == context.tenant.tenant_id]
        items.sort(key=lambda item: (item.due_at, str(item.id)), reverse=True)
        return tuple(items)

    @staticmethod
    def assigned_to_user(
        user_id: UUID,
        follow_ups: list[CustomerFollowUp],
        *,
        tenant_id: UUID | None = None,
        include_completed: bool = True,
        context: RequestContext | None = None,
    ) -> tuple[CustomerFollowUp, ...]:
        """Return assigned follow-ups, filtering to customers within Core scope."""
        items = [item for item in follow_ups if item.assigned_to_user_id == user_id]
        if tenant_id is not None:
            items = [item for item in items if item.tenant_id == tenant_id]
        if not include_completed:
            items = [item for item in items if item.status is not FollowUpStatus.COMPLETED]
        if context is not None:
            items = [
                item
                for item in items
                if str(item.tenant_id) == context.tenant.tenant_id
                and context.can_access_resource(str(item.customer_id))
            ]
        items.sort(key=lambda item: (item.due_at, str(item.id)))
        return tuple(items)

    @staticmethod
    def _validate_customer(follow_up: CustomerFollowUp, customer: Customer) -> None:
        if follow_up.tenant_id != customer.tenant_id:
            raise ValueError("Follow-up and customer must belong to the same tenant")
        if follow_up.customer_id != customer.id:
            raise ValueError("Follow-up customer does not match the supplied customer")

    @staticmethod
    def _require_access(
        follow_up: CustomerFollowUp,
        customer: Customer,
        context: RequestContext | None,
    ) -> None:
        if context is not None:
            FollowUpService.require_access(follow_up, customer, context)
