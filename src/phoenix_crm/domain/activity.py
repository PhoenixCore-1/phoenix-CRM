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


class InteractionDirection(str, Enum):
    """Direction of a communication interaction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ActivitySource(str, Enum):
    """Origin of an activity record."""
    MANUAL = "manual"
    IMPORT = "import"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AI_ASSISTED = "ai_assisted"


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
    direction: InteractionDirection = InteractionDirection.UNKNOWN
    duration_minutes: int | None = None
    source: ActivitySource = ActivitySource.MANUAL
    communication_reference: str | None = None
    participant_user_ids: tuple[UUID, ...] = ()
    participant_contact_ids: tuple[UUID, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("Activity subject cannot be empty")
        self.subject = self.subject.strip()
        if self.notes is not None:
            self.notes = self.notes.strip() or None
        if self.duration_minutes is not None and self.duration_minutes < 0:
            raise ValueError("Activity duration cannot be negative")
        if self.communication_reference is not None:
            self.communication_reference = self.communication_reference.strip() or None
        self.participant_user_ids = tuple(self.participant_user_ids)
        self.participant_contact_ids = tuple(self.participant_contact_ids)
        self.metadata = dict(self.metadata)

    def update_details(self, *, subject: str | None = None, outcome: ActivityOutcome | None = None, notes: str | None = None) -> None:
        """Update activity details while preserving historical occurrence time."""
        if subject is not None:
            if not subject.strip():
                raise ValueError("Activity subject cannot be empty")
            self.subject = subject.strip()
        if outcome is not None:
            self.outcome = outcome
        if notes is not None:
            self.notes = notes.strip() or None
        self.updated_at = datetime.now(timezone.utc)

    def set_relationship_context(self, *, contact_id: UUID | None = None, site_id: UUID | None = None, site_party_id: UUID | None = None) -> None:
        """Set optional CRM relationship context for the activity."""
        self.contact_id = contact_id
        self.site_id = site_id
        self.site_party_id = site_party_id
        self.updated_at = datetime.now(timezone.utc)

    def set_communication_context(self, *, direction: InteractionDirection | None = None, duration_minutes: int | None = None, source: ActivitySource | None = None, communication_reference: str | None = None, participant_user_ids: tuple[UUID, ...] | None = None, participant_contact_ids: tuple[UUID, ...] | None = None, metadata: dict[str, str] | None = None) -> None:
        """Update interaction metadata without replacing the activity itself."""
        if duration_minutes is not None and duration_minutes < 0:
            raise ValueError("Activity duration cannot be negative")
        if direction is not None:
            self.direction = direction
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if source is not None:
            self.source = source
        if communication_reference is not None:
            self.communication_reference = communication_reference.strip() or None
        if participant_user_ids is not None:
            self.participant_user_ids = tuple(participant_user_ids)
        if participant_contact_ids is not None:
            self.participant_contact_ids = tuple(participant_contact_ids)
        if metadata is not None:
            self.metadata = dict(metadata)
        self.updated_at = datetime.now(timezone.utc)
