"""Lead domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class LeadStatus(str, Enum):
    """Initial lifecycle states supported by the CRM lead domain."""

    NEW = "new"


class LeadSource(str, Enum):
    """Origin of a CRM lead."""

    PROJECT_SITE_DISCOVERY = "project_site_discovery"
    REFERRAL = "referral"
    WEBSITE = "website"
    SALES_ACTIVITY = "sales_activity"
    CUSTOMER_REFERRAL = "customer_referral"
    MANUAL_ENTRY = "manual_entry"
    OTHER_MODULE = "other_module"
    OTHER = "other"


@dataclass(slots=True)
class Lead:
    """Tenant-scoped CRM lead awaiting qualification and possible conversion.

    The lead is a CRM-owned relationship record. Source information identifies
    where the lead came from without creating a dependency on the originating
    module or channel implementation.
    """

    tenant_id: UUID
    name: str
    source: LeadSource
    id: UUID = field(default_factory=uuid4)
    status: LeadStatus = LeadStatus.NEW
    assigned_to_user_id: UUID | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    notes: str | None = None
    access_scope_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Lead name cannot be empty")
        self.name = self.name.strip()
        self.company_name = self._clean_optional(self.company_name)
        self.email = self._clean_optional(self.email)
        self.phone = self._clean_optional(self.phone)
        self.mobile = self._clean_optional(self.mobile)
        self.notes = self._clean_optional(self.notes)

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    def rename(self, name: str) -> None:
        """Rename the lead and update its modification timestamp."""
        if not name.strip():
            raise ValueError("Lead name cannot be empty")
        self.name = name.strip()
        self.updated_at = datetime.now(timezone.utc)

    def update_notes(self, notes: str | None) -> None:
        """Replace lead notes while preserving the domain timestamp contract."""
        self.notes = self._clean_optional(notes)
        self.updated_at = datetime.now(timezone.utc)
