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
    """Find likely existing CRM records without automatically merging or linking them."""

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
        """Return same-tenant duplicate candidates ordered by match strength."""
        matches: list[LeadMatch] = []
        for candidate in candidates:
            if candidate.id == lead.id or candidate.tenant_id != lead.tenant_id:
                continue
            fields = cls._lead_fields(lead, candidate)
            non_name_fields = [field for field in fields if field != "name"]
            if not non_name_fields:
                continue
            matches.append(
                LeadMatch(candidate.id, "lead", cls._score(non_name_fields), tuple(fields))
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
                matches.append(LeadMatch(customer.id, "customer", cls._score(fields), tuple(fields)))
        return cls._ordered(matches)

    @classmethod
    def _lead_fields(cls, lead: Lead, candidate: Lead) -> list[str]:
        fields: list[str] = []

        lead_email = cls.normalize(lead.email)
        candidate_email = cls.normalize(candidate.email)
        if lead_email and candidate_email and lead_email == candidate_email:
            fields.append("email")

        lead_phone = cls._phone(lead.phone)
        candidate_phone = cls._phone(candidate.phone)
        if lead_phone and candidate_phone and lead_phone == candidate_phone:
            fields.append("phone")

        lead_mobile = cls._phone(lead.mobile)
        candidate_mobile = cls._phone(candidate.mobile)
        if lead_mobile and candidate_mobile and lead_mobile == candidate_mobile:
            fields.append("mobile")

        lead_name = cls.normalize(lead.name)
        candidate_name = cls.normalize(candidate.name)
        if lead_name and candidate_name and lead_name == candidate_name:
            fields.append("name")

        lead_company = cls.normalize(lead.company_name)
        candidate_company = cls.normalize(candidate.company_name)
        if lead_company and candidate_company and lead_company == candidate_company:
            fields.append("company_name")

        return fields

    @classmethod
    def _customer_fields(cls, lead: Lead, customer: Customer) -> list[str]:
        fields: list[str] = []
        lead_company = cls.normalize(lead.company_name)
        customer_name = cls.normalize(customer.name)
        if lead_company and customer_name and lead_company == customer_name:
            fields.append("company_name")
        else:
            lead_name = cls.normalize(lead.name)
            if lead_name and customer_name and lead_name == customer_name:
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
