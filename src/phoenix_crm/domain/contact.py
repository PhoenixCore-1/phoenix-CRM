"""Contact domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ContactStatus(str, Enum):
    """Lifecycle status of a CRM contact record."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LEFT_COMPANY = "left_company"


@dataclass(slots=True)
class Contact:
    """Tenant-scoped person associated with a CRM customer."""

    tenant_id: UUID
    customer_id: UUID
    first_name: str
    last_name: str
    id: UUID = field(default_factory=uuid4)
    job_title: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    status: ContactStatus = ContactStatus.ACTIVE
    is_primary: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.first_name.strip():
            raise ValueError("Contact first name cannot be empty")
        if not self.last_name.strip():
            raise ValueError("Contact last name cannot be empty")
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        if self.job_title is not None:
            self.job_title = self.job_title.strip() or None
        if self.email is not None:
            self.email = self.email.strip() or None
        if self.phone is not None:
            self.phone = self.phone.strip() or None
        if self.mobile is not None:
            self.mobile = self.mobile.strip() or None

    @property
    def full_name(self) -> str:
        """Return the contact's display name."""
        return f"{self.first_name} {self.last_name}"

    def rename(self, first_name: str, last_name: str) -> None:
        """Rename the contact and update its modification timestamp."""
        if not first_name.strip():
            raise ValueError("Contact first name cannot be empty")
        if not last_name.strip():
            raise ValueError("Contact last name cannot be empty")
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.updated_at = datetime.now(timezone.utc)

    def set_primary(self, is_primary: bool) -> None:
        """Set whether this contact is designated as the primary contact."""
        self.is_primary = is_primary
        self.updated_at = datetime.now(timezone.utc)
