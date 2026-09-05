"""Project-site party matching services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from phoenix_crm.domain import Customer, ProjectSiteParty


class MatchOutcome(str, Enum):
    """Result of evaluating a site party against CRM customers."""

    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"


@dataclass(frozen=True, slots=True)
class CustomerMatch:
    """A candidate CRM customer returned by the matching service."""

    customer_id: UUID
    score: float


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Deterministic result of a project-site party matching operation."""

    outcome: MatchOutcome
    candidates: tuple[CustomerMatch, ...] = ()


class SitePartyMatchingService:
    """Match discovered site parties to tenant-scoped CRM customers.

    This service deliberately performs suggestion/matching only. It never
    creates customers and never links a customer automatically. Linking is an
    explicit CRM action after an unambiguous candidate has been identified.
    """

    def find_candidates(
        self,
        party: ProjectSiteParty,
        customers: list[Customer],
    ) -> MatchResult:
        """Return same-tenant candidates using normalized exact-name matching."""
        normalized_party = self.normalize_name(party.name)
        candidates = [
            CustomerMatch(customer.id, 1.0)
            for customer in customers
            if customer.tenant_id == party.tenant_id
            and self.normalize_name(customer.name) == normalized_party
        ]
        candidates.sort(key=lambda candidate: str(candidate.customer_id))
        if len(candidates) == 1:
            return MatchResult(MatchOutcome.MATCHED, tuple(candidates))
        if len(candidates) > 1:
            return MatchResult(MatchOutcome.AMBIGUOUS, tuple(candidates))
        return MatchResult(MatchOutcome.NO_MATCH)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a party/customer name for deterministic matching."""
        return " ".join(name.casefold().split())

    @staticmethod
    def link_match(party: ProjectSiteParty, customer: Customer) -> None:
        """Explicitly link a party to a customer after validating tenant scope."""
        if party.tenant_id != customer.tenant_id:
            raise ValueError("Cannot link a site party to a customer from another tenant")
        party.link_customer(customer.id)
