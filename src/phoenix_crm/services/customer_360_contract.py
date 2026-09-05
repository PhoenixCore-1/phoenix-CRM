"""Customer 360 aggregate/view contract for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerStatus


@dataclass(frozen=True, slots=True)
class Customer360Reference:
    """A lightweight reference to a related resource owned by CRM or another module."""

    module_code: str
    resource_type: str
    resource_id: UUID
    label: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        if not self.module_code.strip():
            raise ValueError("module_code cannot be empty")
        if not self.resource_type.strip():
            raise ValueError("resource_type cannot be empty")


@dataclass(frozen=True, slots=True)
class Customer360View:
    """Immutable Customer 360 read contract.

    This is a presentation/read model, not a new business-domain aggregate.
    CRM remains authoritative for CRM-owned customer relationships, while
    references to other modules remain lightweight and contract-based.
    """

    tenant_id: UUID
    customer_id: UUID
    customer_name: str
    customer_status: CustomerStatus
    customer_type_id: UUID
    call_class_id: UUID
    account_owner_id: UUID | None
    access_scope_id: UUID | None
    primary_contact_id: UUID | None = None
    last_interaction_at: datetime | None = None
    next_interaction_at: datetime | None = None
    relationship_health: str | None = None
    contact_ids: tuple[UUID, ...] = ()
    site_ids: tuple[UUID, ...] = ()
    references: tuple[Customer360Reference, ...] = ()

    def __post_init__(self) -> None:
        if not self.customer_name.strip():
            raise ValueError("customer_name cannot be empty")

    @classmethod
    def from_customer(
        cls,
        customer: Customer,
        *,
        primary_contact_id: UUID | None = None,
        last_interaction_at: datetime | None = None,
        next_interaction_at: datetime | None = None,
        relationship_health: str | None = None,
        references: tuple[Customer360Reference, ...] = (),
    ) -> "Customer360View":
        """Build a read projection without changing the Customer aggregate."""
        return cls(
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            customer_name=customer.name,
            customer_status=customer.status,
            customer_type_id=customer.customer_type_id,
            call_class_id=customer.call_class_id,
            account_owner_id=customer.account_owner_id,
            access_scope_id=customer.access_scope_id,
            primary_contact_id=primary_contact_id,
            last_interaction_at=last_interaction_at,
            next_interaction_at=next_interaction_at,
            relationship_health=relationship_health,
            contact_ids=tuple(sorted(customer.contact_ids, key=str)),
            site_ids=tuple(sorted(customer.site_ids, key=str)),
            references=tuple(references),
        )
