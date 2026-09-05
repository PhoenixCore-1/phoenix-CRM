"""Complete Customer 360 composition boundary for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Customer
from phoenix_crm.services.customer_360_contract import Customer360View
from phoenix_crm.services.customer_360_documents import Customer360DocumentsSection
from phoenix_crm.services.customer_360_overview import Customer360Overview
from phoenix_crm.services.customer_360_contacts_sites import Customer360ContactsSitesSection
from phoenix_crm.services.customer_360_projects import Customer360ProjectSiteSection
from phoenix_crm.services.customer_360_purchase import Customer360PurchaseSection
from phoenix_crm.services.customer_360_potential import Customer360PotentialSection
from phoenix_crm.services.customer_360_timeline import Customer360Timeline


@dataclass(frozen=True, slots=True)
class Customer360Composition:
    """Immutable complete Customer 360 read model."""

    view: Customer360View
    overview: Customer360Overview
    timeline: Customer360Timeline
    purchases: Customer360PurchaseSection
    potential: Customer360PotentialSection
    contacts_sites: Customer360ContactsSitesSection
    projects_sites: Customer360ProjectSiteSection
    documents: Customer360DocumentsSection

    @property
    def tenant_id(self) -> UUID:
        return self.view.tenant_id

    @property
    def customer_id(self) -> UUID:
        return self.view.customer_id


class Customer360CompositionService:
    """Validate and compose already-built Customer 360 sections.

    This service owns composition only. Section ownership remains with the
    existing CRM services and published capability boundaries.
    """

    @staticmethod
    def build(
        *,
        customer: Customer,
        view: Customer360View,
        overview: Customer360Overview,
        timeline: Customer360Timeline,
        purchases: Customer360PurchaseSection,
        potential: Customer360PotentialSection,
        contacts_sites: Customer360ContactsSitesSection,
        projects_sites: Customer360ProjectSiteSection,
        documents: Customer360DocumentsSection,
        request_context: RequestContext | None = None,
    ) -> Customer360Composition:
        if customer.tenant_id != view.tenant_id or customer.id != view.customer_id:
            raise ValueError("Customer and Customer 360 view do not match")
        Customer360CompositionService._require_access(customer, request_context)

        sections = (
            overview,
            timeline,
            purchases,
            potential,
            contacts_sites,
            projects_sites,
            documents,
        )
        for section in sections:
            if section.tenant_id != customer.tenant_id or section.customer_id != customer.id:
                raise ValueError("Customer 360 section does not match customer")

        return Customer360Composition(
            view=view,
            overview=overview,
            timeline=timeline,
            purchases=purchases,
            potential=potential,
            contacts_sites=contacts_sites,
            projects_sites=projects_sites,
            documents=documents,
        )

    @staticmethod
    def _require_access(customer: Customer, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(customer.tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer.id)):
            raise PermissionError("Core access scope does not include this customer")
