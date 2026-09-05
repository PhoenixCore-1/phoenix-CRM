"""Project-site party relationship domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class SitePartyRole(str, Enum):
    """Role a party may have on a project site."""

    MAIN_CONTRACTOR = "main_contractor"
    SUBCONTRACTOR = "subcontractor"
    ELECTRICAL_CONTRACTOR = "electrical_contractor"
    PLUMBING_CONTRACTOR = "plumbing_contractor"
    HVAC_CONTRACTOR = "hvac_contractor"
    ENGINEER = "engineer"
    ARCHITECT = "architect"
    SUPPLIER = "supplier"
    OTHER = "other"


class SitePartyMatchStatus(str, Enum):
    """CRM matching state for a discovered project-site party."""

    UNMATCHED = "unmatched"
    MATCHED_CUSTOMER = "matched_customer"
    POTENTIAL_LEAD = "potential_lead"


class SitePartySource(str, Enum):
    """Source through which CRM discovered a project-site party."""

    PROJECT_SITE_DISCOVERY = "project_site_discovery"
    REFERRAL = "referral"
    SALES_ACTIVITY = "sales_activity"
    MANUAL_ENTRY = "manual_entry"
    OTHER_MODULE = "other_module"
    OTHER = "other"


class SitePartyStatus(str, Enum):
    """Lifecycle status of a CRM project-site party relationship."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"


@dataclass(slots=True)
class ProjectSiteParty:
    """CRM relationship record for a party discovered on a project site.

    Project and project-site identifiers are external references owned by
    Phoenix Projects 360. CRM stores the relationship intelligence only and
    does not duplicate the authoritative project/site entities.
    """

    tenant_id: UUID
    project_id: UUID
    project_site_id: UUID
    name: str
    role: SitePartyRole
    source: SitePartySource = SitePartySource.PROJECT_SITE_DISCOVERY
    id: UUID = field(default_factory=uuid4)
    customer_id: UUID | None = None
    match_status: SitePartyMatchStatus = SitePartyMatchStatus.UNMATCHED
    status: SitePartyStatus = SitePartyStatus.ACTIVE
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Site party name cannot be empty")
        self.name = self.name.strip()
        if self.notes is not None:
            self.notes = self.notes.strip() or None
        if self.customer_id is not None and self.match_status is SitePartyMatchStatus.UNMATCHED:
            self.match_status = SitePartyMatchStatus.MATCHED_CUSTOMER

    def link_customer(self, customer_id: UUID) -> None:
        """Link the discovered party to an existing CRM customer."""
        self.customer_id = customer_id
        self.match_status = SitePartyMatchStatus.MATCHED_CUSTOMER
        self.status = SitePartyStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def mark_potential_lead(self) -> None:
        """Mark the party as requiring CRM lead qualification."""
        self.customer_id = None
        self.match_status = SitePartyMatchStatus.POTENTIAL_LEAD
        self.status = SitePartyStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def clear_match(self) -> None:
        """Remove the current customer/lead match and return to unmatched."""
        self.customer_id = None
        self.match_status = SitePartyMatchStatus.UNMATCHED
        self.updated_at = datetime.now(timezone.utc)

    def update_notes(self, notes: str | None) -> None:
        """Update relationship notes."""
        self.notes = notes.strip() if notes is not None and notes.strip() else None
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Mark the relationship inactive without deleting its history."""
        self.status = SitePartyStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self) -> None:
        """Restore an inactive relationship to active status."""
        self.status = SitePartyStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def remove(self) -> None:
        """Mark the relationship removed while preserving its record."""
        self.status = SitePartyStatus.REMOVED
        self.updated_at = datetime.now(timezone.utc)
