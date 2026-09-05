"""Customer potential qualification services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import (
    CustomerPotential,
    PotentialPriority,
    PotentialStatus,
)


@dataclass(frozen=True, slots=True)
class PotentialQualificationResult:
    """Outcome of a customer potential lifecycle operation."""

    potential_id: UUID
    status: PotentialStatus
    changed: bool


class PotentialQualificationService:
    """Orchestrate CRM potential lifecycle operations."""

    @staticmethod
    def start(potential: CustomerPotential) -> PotentialQualificationResult:
        """Start qualification for an identified potential."""
        potential.start_qualification()
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def qualify(potential: CustomerPotential) -> PotentialQualificationResult:
        """Qualify an identified or qualifying potential."""
        potential.qualify()
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def realize(potential: CustomerPotential) -> PotentialQualificationResult:
        """Mark a qualified potential as realized."""
        potential.realize()
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def decline(potential: CustomerPotential) -> PotentialQualificationResult:
        """Decline an active potential."""
        potential.decline()
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def close(potential: CustomerPotential) -> PotentialQualificationResult:
        """Close a non-terminal potential."""
        potential.close()
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def set_priority(
        potential: CustomerPotential,
        priority: PotentialPriority,
    ) -> PotentialQualificationResult:
        """Change potential priority."""
        potential.set_priority(priority)
        return PotentialQualificationResult(potential.id, potential.status, True)

    @staticmethod
    def update_context(
        potential: CustomerPotential,
        *,
        reason: str,
        context: str | None = None,
    ) -> PotentialQualificationResult:
        """Update the reason and context supporting the potential."""
        potential.update_context(reason, context)
        return PotentialQualificationResult(potential.id, potential.status, True)
