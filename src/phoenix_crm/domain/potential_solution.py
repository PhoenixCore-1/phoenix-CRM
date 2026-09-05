"""Potential and current solution domain objects for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class SolutionRelationship(str, Enum):
    """How a solution relates to the customer's current or potential state."""

    CURRENT = "current"
    POTENTIAL = "potential"


class SolutionStatus(str, Enum):
    """Lifecycle status of a customer solution relationship."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


@dataclass(slots=True)
class CustomerSolution:
    """A CRM-owned relationship between a customer and a solution.

    CRM records relationship intelligence only. Commercial opportunities,
    quotes, pricing and orders remain owned by the Sales module.
    """

    tenant_id: UUID
    customer_id: UUID
    solution_name: str
    relationship: SolutionRelationship
    id: UUID = field(default_factory=uuid4)
    status: SolutionStatus = SolutionStatus.ACTIVE
    reason: str | None = None
    source: str | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.solution_name = self.solution_name.strip()
        if not self.solution_name:
            raise ValueError("Solution name cannot be empty")
        self.reason = self._clean_optional(self.reason)
        self.source = self._clean_optional(self.source)
        self.notes = self._clean_optional(self.notes)

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def rename(self, solution_name: str) -> None:
        """Rename the solution relationship."""
        solution_name = solution_name.strip()
        if not solution_name:
            raise ValueError("Solution name cannot be empty")
        self.solution_name = solution_name
        self.updated_at = datetime.now(timezone.utc)

    def update_context(
        self,
        *,
        reason: str | None = None,
        source: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Update relationship context without changing its identity."""
        self.reason = self._clean_optional(reason)
        self.source = self._clean_optional(source)
        self.notes = self._clean_optional(notes)
        self.updated_at = datetime.now(timezone.utc)

    def mark_inactive(self) -> None:
        """Mark the relationship inactive while preserving its history."""
        self.status = SolutionStatus.INACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self) -> None:
        """Reactivate an inactive relationship."""
        if self.status is SolutionStatus.CLOSED:
            raise ValueError("Closed solution relationships cannot be reactivated")
        self.status = SolutionStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        """Close the relationship without deleting historical context."""
        self.status = SolutionStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)
