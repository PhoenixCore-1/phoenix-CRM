"""Integrity validation for Phoenix CRM 360 activities."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import Contact, Customer, CustomerActivity, CustomerSite, ProjectSiteParty


@dataclass(frozen=True, slots=True)
class ActivityValidationResult:
    """Result of validating an activity against known CRM relationships."""

    valid: bool
    errors: tuple[str, ...] = ()


class ActivityIntegrityService:
    """Validate activity relationships without owning external module data."""

    @staticmethod
    def validate(
        activity: CustomerActivity,
        customer: Customer,
        *,
        contact: Contact | None = None,
        site: CustomerSite | None = None,
        site_party: ProjectSiteParty | None = None,
    ) -> ActivityValidationResult:
        errors: list[str] = []

        if activity.tenant_id != customer.tenant_id:
            errors.append("Activity and customer must belong to the same tenant")
        if activity.customer_id != customer.id:
            errors.append("Activity customer does not match the supplied customer")

        if activity.contact_id is not None:
            if contact is None:
                errors.append("Activity contact context requires the matching contact")
            else:
                if contact.id != activity.contact_id:
                    errors.append("Activity contact does not match the supplied contact")
                if contact.tenant_id != customer.tenant_id:
                    errors.append("Activity contact must belong to the same tenant")
                if contact.customer_id != customer.id:
                    errors.append("Activity contact must belong to the activity customer")

        if activity.site_id is not None:
            if site is None:
                errors.append("Activity site context requires the matching site")
            else:
                if site.id != activity.site_id:
                    errors.append("Activity site does not match the supplied site")
                if site.tenant_id != customer.tenant_id:
                    errors.append("Activity site must belong to the same tenant")
                if site.customer_id != customer.id:
                    errors.append("Activity site must belong to the activity customer")

        if activity.site_party_id is not None:
            if site_party is None:
                errors.append("Activity site-party context requires the matching site party")
            else:
                if site_party.id != activity.site_party_id:
                    errors.append("Activity site party does not match the supplied site party")
                if site_party.tenant_id != customer.tenant_id:
                    errors.append("Activity site party must belong to the same tenant")
                if site_party.customer_id is not None and site_party.customer_id != customer.id:
                    errors.append("Activity site party must belong to the activity customer")

        return ActivityValidationResult(valid=not errors, errors=tuple(errors))

    @staticmethod
    def require_valid(
        activity: CustomerActivity,
        customer: Customer,
        *,
        contact: Contact | None = None,
        site: CustomerSite | None = None,
        site_party: ProjectSiteParty | None = None,
    ) -> None:
        """Raise ValueError when activity relationship integrity fails."""
        result = ActivityIntegrityService.validate(
            activity,
            customer,
            contact=contact,
            site=site,
            site_party=site_party,
        )
        if not result.valid:
            raise ValueError("; ".join(result.errors))
