"""Customer relationship activity domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ActivityType(str, Enum):
    """Type of customer relationship interaction."""

    CALL = "call"
    MEETING = "meeting"
    SITE_VISIT = "site_visit"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    NOTE = "note"
    OTHER = "other"


class ActivityOutcome(str, Enum):
    """Outcome of a completed customer relationship activity."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    NO_RESPONSE = "no_response"
    FOLLOW_UP_REQUIRED = "follow_up_required"


@dataclass(slots=True)
class CustomerActivity:
    """Tenant-scoped historical interaction with a CRM customer."""

    tenant_id: UUID
    customer_id: UUID
    activity_type: ActivityType
    subject: str
    occurred_at: datetime
    id: UUID = field(default_factory=uuid4)
    contact_id: UUID | None = None
    site_id: UUID | None = None
    site_party_id: UUID | None = None
    performed_by_user_id: UUID | None = None
    outcome: ActivityOutcome | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("Activity subject cannot be empty")
        self.subject = self.subject.strip()
        if self.notes is not None:
            self.notes = self.notes.strip() or None

    def update_details(
        self,
        *,
        subject: str | None = None,
        outcome: ActivityOutcome | None = None,
        notes: str | None = None,
    ) -> None:
        """Update activity details while preserving its historical occurrence time."""
        if subject is not None:
            if not subject.strip():
                raise ValueError("Activity subject cannot be empty")
            self.subject = subject.strip()
        if outcome is not None:
            self.outcome = outcome
        if notes is not None:
            self.notes = notes.strip() or None
        self.updated_at = datetime.now(timezone.utc)

    def set_relationship_context(
        self,
        *,
        contact_id: UUID | None = None,
        site_id: UUID | None = None,
        site_party_id: UUID | None = None,
    ) -> None:
        """Set optional CRM relationship context for the activity."""
        self.contact_id = contact_id
        self.site_id = site_id
        self.site_party_id = site_party_id
        self.updated_at = datetime.now(timezone.utc)
