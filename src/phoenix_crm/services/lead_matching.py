"""Lead duplicate detection and customer matching for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import Customer, Lead


@dataclass(frozen=True, slots=True)
class LeadMatch:
    """A deterministic candidate match with the fields that caused it."""

    entity_id: UUID
    entity_type: str
    score: int
    matched_fields: tuple[str, ...]


class LeadMatchingService:
    """Find likely existing CRM records without automatically merging or linking them.

    Matching is intentionally deterministic and conservative. Tenant isolation is
    enforced before comparing records, and callers remain responsible for the
    final duplicate decision or customer link.
    """

    @staticmethod
    def normalize(value: str | None) -> str:
        """Normalize a comparison value for deterministic matching."""
        if not value:
            return ""
        return " ".join(value.casefold().strip().split())

    @classmethod
    def lead_duplicates(
        cls,
        lead: Lead,
        candidates: list[Lead] | tuple[Lead, ...],
    ) -> list[LeadMatch]:
        """Return same-tenant lead candidates ordered by strongest match."""
        matches: list[LeadMatch] = []
        for candidate in candidates:
            if candidate.id == lead.id or candidate.tenant_id != lead.tenant_id:
                continue
            fields = cls._lead_fields(lead, candidate)
            if fields:
                matches.append(
                    LeadMatch(candidate.id, "lead", cls._score(fields), tuple(fields))
                )
        return cls._ordered(matches)

    @classmethod
    def customer_matches(
        cls,
        lead: Lead,
        customers: list[Customer] | tuple[Customer, ...],
    ) -> list[LeadMatch]:
        """Return same-tenant customer candidates for a lead."""
        matches: list[LeadMatch] = []
        for customer in customers:
            if customer.tenant_id != lead.tenant_id:
                continue
            fields = cls._customer_fields(lead, customer)
            if fields:
                matches.append(
                    LeadMatch(customer.id, "customer", cls._score(fields), tuple(fields))
                )
        return cls._ordered(matches)

    @classmethod
    def _lead_fields(cls, lead: Lead, candidate: Lead) -> list[str]:
        fields: list[str] = []
        if cls.normalize(lead.name) == cls.normalize(candidate.name):
            fields.append("name")
        if lead.email and cls.normalize(lead.email) == cls.normalize(candidate.email):
            fields.append("email")
        if lead.phone and cls._phone(lead.phone) == cls._phone(candidate.phone):
            fields.append("phone")
        if lead.mobile and cls._phone(lead.mobile) == cls._phone(candidate.mobile):
            fields.append("mobile")
        if lead.company_name and cls.normalize(lead.company_name) == cls.normalize(candidate.company_name):
            fields.append("company_name")
        return fields

    @classmethod
    def _customer_fields(cls, lead: Lead, customer: Customer) -> list[str]:
        fields: list[str] = []
        if lead.company_name and cls.normalize(lead.company_name) == cls.normalize(customer.name):
            fields.append("company_name")
        elif cls.normalize(lead.name) == cls.normalize(customer.name):
            fields.append("name")
        return fields

    @staticmethod
    def _phone(value: str | None) -> str:
        if not value:
            return ""
        return "".join(character for character in value if character.isdigit())

    @staticmethod
    def _score(fields: list[str]) -> int:
        weights = {"email": 100, "phone": 90, "mobile": 90, "company_name": 60, "name": 50}
        return sum(weights[field] for field in fields)

    @staticmethod
    def _ordered(matches: list[LeadMatch]) -> list[LeadMatch]:
        return sorted(matches, key=lambda match: (-match.score, str(match.entity_id)))
