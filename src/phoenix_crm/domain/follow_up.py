"""First-class customer follow-up domain model for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class FollowUpStatus(str, Enum):
    """Lifecycle status of a CRM follow-up."""

    PLANNED = "planned"
    DUE = "due"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class FollowUpPriority(str, Enum):
    """Priority of a CRM follow-up."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(slots=True)
class CustomerFollowUp:
    """Tenant-scoped action to continue a CRM customer relationship."""

    tenant_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID
    due_at: datetime
    reason: str
    id: UUID = field(default_factory=uuid4)
    contact_id: UUID | None = None
    site_id: UUID | None = None
    site_party_id: UUID | None = None
    related_activity_id: UUID | None = None
    priority: FollowUpPriority = FollowUpPriority.NORMAL
    status: FollowUpStatus = FollowUpStatus.PLANNED
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Follow-up reason cannot be empty")
        self.reason = self.reason.strip()
        if self.notes is not None:
            self.notes = self.notes.strip() or None

    def complete(self, *, completed_at: datetime | None = None) -> None:
        """Complete the follow-up and record its completion time."""
        if self.status in {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED}:
            raise ValueError("Only active follow-ups can be completed")
        self.status = FollowUpStatus.COMPLETED
        self.completed_at = completed_at or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Cancel an active follow-up."""
        if self.status in {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED}:
            raise ValueError("Only active follow-ups can be cancelled")
        self.status = FollowUpStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def reschedule(self, due_at: datetime) -> None:
        """Move an active follow-up to a new due date/time."""
        if self.status in {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED}:
            raise ValueError("Only active follow-ups can be rescheduled")
        self.due_at = due_at
        self.status = FollowUpStatus.RESCHEDULED
        self.updated_at = datetime.now(timezone.utc)

    def mark_due(self) -> None:
        """Mark an active follow-up as due."""
        if self.status in {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED}:
            raise ValueError("Only active follow-ups can be marked due")
        self.status = FollowUpStatus.DUE
        self.updated_at = datetime.now(timezone.utc)
