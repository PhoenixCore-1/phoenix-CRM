"""Lead qualification services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import Lead, LeadStatus


@dataclass(frozen=True, slots=True)
class LeadQualificationResult:
    """Result of a CRM lead qualification operation."""

    lead_id: UUID
    status: LeadStatus
    qualified: bool
    rationale: str | None = None


class LeadQualificationService:
    """Coordinate controlled CRM lead qualification without external modules."""

    @staticmethod
    def start(lead: Lead) -> LeadQualificationResult:
        """Start qualification for a new lead."""
        lead.start_qualification()
        return LeadQualificationService._result(lead, qualified=False)

    @staticmethod
    def qualify(
        lead: Lead,
        *,
        rationale: str | None = None,
    ) -> LeadQualificationResult:
        """Mark a lead as qualified after CRM qualification work is complete."""
        if rationale is not None and not rationale.strip():
            raise ValueError("rationale cannot be empty")
        lead.qualify()
        cleaned_rationale = rationale.strip() if rationale is not None else None
        return LeadQualificationService._result(
            lead,
            qualified=True,
            rationale=cleaned_rationale,
        )

    @staticmethod
    def mark_potential_customer(lead: Lead) -> LeadQualificationResult:
        """Advance a qualified lead to the potential-customer state."""
        lead.mark_potential_customer()
        return LeadQualificationService._result(lead, qualified=True)

    @staticmethod
    def disqualify(
        lead: Lead,
        *,
        rationale: str | None = None,
    ) -> LeadQualificationResult:
        """Disqualify a lead while preserving the reason supplied by the caller."""
        if rationale is not None and not rationale.strip():
            raise ValueError("rationale cannot be empty")
        lead.disqualify()
        cleaned_rationale = rationale.strip() if rationale is not None else None
        return LeadQualificationService._result(
            lead,
            qualified=False,
            rationale=cleaned_rationale,
        )

    @staticmethod
    def _result(
        lead: Lead,
        *,
        qualified: bool,
        rationale: str | None = None,
    ) -> LeadQualificationResult:
        return LeadQualificationResult(
            lead_id=lead.id,
            status=lead.status,
            qualified=qualified,
            rationale=rationale,
        )
