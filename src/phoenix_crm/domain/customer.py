"""Customer domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class CustomerStatus(str, Enum):
    """Lifecycle status of a CRM customer record."""

    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on_hold"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class CustomerType:
    """Configurable classification describing what kind of customer this is."""

    id: UUID
    name: str
    code: str
    active: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Customer type name cannot be empty")
        if not self.code.strip():
            raise ValueError("Customer type code cannot be empty")


@dataclass(frozen=True, slots=True)
class CallCadence:
    """Configurable customer-contact cadence expressed in days."""

    interval_days: int | None

    def __post_init__(self) -> None:
        if self.interval_days is not None and self.interval_days <= 0:
            raise ValueError("Call cadence interval must be positive")


@dataclass(frozen=True, slots=True)
class CustomerCallClass:
    """Configurable call class that determines relationship contact cadence."""

    id: UUID
    name: str
    code: str
    cadence: CallCadence
    active: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Call class name cannot be empty")
        if not self.code.strip():
            raise ValueError("Call class code cannot be empty")


@dataclass(slots=True)
class Customer:
    """Tenant-scoped CRM customer relationship record.

    Core remains authoritative for tenant identity and access scope. The CRM
    domain stores only the Core identifiers it needs to apply business rules.
    """

    tenant_id: UUID
    name: str
    customer_type_id: UUID
    call_class_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: CustomerStatus = CustomerStatus.ACTIVE
    account_owner_id: UUID | None = None
    access_scope_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Customer name cannot be empty")
        self.name = self.name.strip()

    def rename(self, name: str) -> None:
        """Rename the customer and update its modification timestamp."""
        if not name.strip():
            raise ValueError("Customer name cannot be empty")
        self.name = name.strip()
        self.updated_at = datetime.now(timezone.utc)
