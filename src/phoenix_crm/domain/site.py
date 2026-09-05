"""Customer site domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class CustomerSiteStatus(str, Enum):
    """Lifecycle status of a CRM customer site relationship."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


@dataclass(slots=True)
class CustomerSite:
    """Tenant-scoped site/location associated with a CRM customer.

    This represents the customer's CRM relationship to a location. It is not
    the authoritative project-site record owned by Phoenix Projects 360.
    """

    tenant_id: UUID
    customer_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    status: CustomerSiteStatus = CustomerSiteStatus.ACTIVE
    is_primary: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Customer site name cannot be empty")
        self.name = self.name.strip()
        for field_name in (
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
        ):
            value = getattr(self, field_name)
            if value is not None:
                setattr(self, field_name, value.strip() or None)

    def rename(self, name: str) -> None:
        """Rename the customer site and update its modification timestamp."""
        if not name.strip():
            raise ValueError("Customer site name cannot be empty")
        self.name = name.strip()
        self.updated_at = datetime.now(timezone.utc)

    def set_primary(self, is_primary: bool) -> None:
        """Set whether this site is designated as the customer's primary site."""
        self.is_primary = is_primary
        self.updated_at = datetime.now(timezone.utc)
