"""Lead-to-customer conversion services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import Customer, CustomerStatus, Lead, LeadStatus
from phoenix_crm.services.lead_matching import LeadMatch, LeadMatchingService


@dataclass(frozen=True, slots=True)
class CustomerConversionResult:
    """Outcome of evaluating or completing CRM lead conversion."""

    lead_id: UUID
    converted: bool
    customer_id: UUID | None
    existing_customer_matches: tuple[LeadMatch, ...]


class LeadConversionService:
    """Perform conservative duplicate-aware lead conversion inside CRM."""

    @staticmethod
    def evaluate(
        lead: Lead,
        customers: list[Customer] | tuple[Customer, ...],
    ) -> CustomerConversionResult:
        """Evaluate conversion readiness without changing the lead."""
        matches = tuple(LeadMatchingService.customer_matches(lead, customers))
        return CustomerConversionResult(
            lead_id=lead.id,
            converted=False,
            customer_id=None,
            existing_customer_matches=matches,
        )

    @staticmethod
    def convert(
        lead: Lead,
        customers: list[Customer] | tuple[Customer, ...],
        *,
        customer_type_id: UUID,
        call_class_id: UUID,
        duplicate_override_approved: bool = False,
        account_owner_id: UUID | None = None,
        access_scope_id: UUID | None = None,
    ) -> tuple[Customer, CustomerConversionResult]:
        """Convert a potential-customer lead into a new CRM customer.

        Conversion is intentionally conservative. A lead must be in the
        POTENTIAL_CUSTOMER state. Existing customer matches block conversion
        unless an explicit duplicate-review override has been approved by the
        calling workflow. This service never merges or links existing records.
        """
        if lead.status is not LeadStatus.POTENTIAL_CUSTOMER:
            raise ValueError("Only potential customer leads can be converted")

        matches = tuple(LeadMatchingService.customer_matches(lead, customers))
        if matches and not duplicate_override_approved:
            raise ValueError("Potential duplicate customer matches must be resolved before conversion")

        customer = Customer(
            tenant_id=lead.tenant_id,
            name=lead.company_name or lead.name,
            customer_type_id=customer_type_id,
            call_class_id=call_class_id,
            status=CustomerStatus.PROSPECT,
            account_owner_id=account_owner_id or lead.assigned_to_user_id,
            access_scope_id=access_scope_id or lead.access_scope_id,
        )

        # The lead changes state only after the new customer has been
        # successfully constructed. Persistence remains the caller's concern.
        lead.convert()

        return customer, CustomerConversionResult(
            lead_id=lead.id,
            converted=True,
            customer_id=customer.id,
            existing_customer_matches=matches,
        )
