"""Customer potential domain objects for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class PotentialStatus(str, Enum):
    """Lifecycle status of a customer potential record."""

    IDENTIFIED = "identified"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    REALIZED = "realized"
    DECLINED = "declined"
    CLOSED = "closed"


class PotentialPriority(str, Enum):
    """Business priority assigned to a customer potential."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PotentialSource(str, Enum):
    """Source through which customer potential was identified."""

    CUSTOMER_ACTIVITY = "customer_activity"
    SALES_ACTIVITY = "sales_activity"
    PROJECT_SITE = "project_site"
    CUSTOMER_REQUEST = "customer_request"
    AI_ASSISTED = "ai_assisted"
    MANUAL_ENTRY = "manual_entry"
    OTHER_MODULE = "other_module"
    OTHER = "other"


@dataclass(slots=True)
class CustomerPotential:
    """A CRM-owned record of a solution/product potential for a customer.

    CRM identifies, qualifies and manages the relationship opportunity. Sales
    remains authoritative for commercial opportunities, pricing, quotes and
    orders. This object therefore contains relationship intelligence rather
    than commercial transaction data.
    """

    tenant_id: UUID
    customer_id: UUID
    solution_name: str
    reason: str
    source: PotentialSource
    id: UUID = field(default_factory=uuid4)
    status: PotentialStatus = PotentialStatus.IDENTIFIED
    priority: PotentialPriority = PotentialPriority.NORMAL
    context: str | None = None
    current_solution: str | None = None
    assigned_to_user_id: UUID | None = None
    related_activity_ids: set[UUID] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.solution_name.strip():
            raise ValueError("Potential solution name cannot be empty")
        if not self.reason.strip():
            raise ValueError("Potential reason cannot be empty")
        self.solution_name = self.solution_name.strip()
        self.reason = self.reason.strip()
        if self.context is not None:
            self.context = self.context.strip() or None
        if self.current_solution is not None:
            self.current_solution = self.current_solution.strip() or None

    def qualify(self) -> None:
        """Mark an identified/qualifying potential as qualified."""
        if self.status not in {PotentialStatus.IDENTIFIED, PotentialStatus.QUALIFYING}:
            raise ValueError("Only identified or qualifying potential can be qualified")
        self.status = PotentialStatus.QUALIFIED
        self.updated_at = datetime.now(timezone.utc)

    def start_qualification(self) -> None:
        """Move an identified potential into qualification."""
        if self.status is not PotentialStatus.IDENTIFIED:
            raise ValueError("Only identified potential can start qualification")
        self.status = PotentialStatus.QUALIFYING
        self.updated_at = datetime.now(timezone.utc)

    def realize(self) -> None:
        """Mark a qualified potential as realized."""
        if self.status is not PotentialStatus.QUALIFIED:
            raise ValueError("Only qualified potential can be realized")
        self.status = PotentialStatus.REALIZED
        self.updated_at = datetime.now(timezone.utc)

    def decline(self) -> None:
        """Decline an identified, qualifying or qualified potential."""
        if self.status not in {
            PotentialStatus.IDENTIFIED,
            PotentialStatus.QUALIFYING,
            PotentialStatus.QUALIFIED,
        }:
            raise ValueError("Only active potential can be declined")
        self.status = PotentialStatus.DECLINED
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        """Close a potential without implying a commercial outcome."""
        if self.status in {PotentialStatus.REALIZED, PotentialStatus.DECLINED, PotentialStatus.CLOSED}:
            raise ValueError("Potential is already terminal")
        self.status = PotentialStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)

    def set_priority(self, priority: PotentialPriority) -> None:
        """Change potential priority."""
        self.priority = priority
        self.updated_at = datetime.now(timezone.utc)

    def update_context(self, reason: str, context: str | None = None) -> None:
        """Update the relationship context behind the potential."""
        if not reason.strip():
            raise ValueError("Potential reason cannot be empty")
        self.reason = reason.strip()
        self.context = context.strip() if context and context.strip() else None
        self.updated_at = datetime.now(timezone.utc)

    def link_activity(self, activity_id: UUID) -> None:
        """Associate an existing CRM activity with this potential."""
        self.related_activity_ids.add(activity_id)
        self.updated_at = datetime.now(timezone.utc)

    def unlink_activity(self, activity_id: UUID) -> None:
        """Remove an activity association from this potential."""
        self.related_activity_ids.discard(activity_id)
        self.updated_at = datetime.now(timezone.utc)
