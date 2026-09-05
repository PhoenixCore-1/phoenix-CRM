"""Customer 360 contacts and sites presentation for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Contact, ContactStatus, CustomerSite, CustomerSiteStatus


@dataclass(frozen=True, slots=True)
class Customer360ContactItem:
    """Read-only contact presentation item."""

    contact_id: UUID
    full_name: str
    job_title: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    status: ContactStatus
    primary: bool


@dataclass(frozen=True, slots=True)
class Customer360SiteItem:
    """Read-only customer-site presentation item."""

    site_id: UUID
    name: str
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    province: str | None
    postal_code: str | None
    country: str | None
    status: CustomerSiteStatus
    primary: bool


@dataclass(frozen=True, slots=True)
class Customer360ContactsSitesSection:
    """Read-only Contacts and Sites section for Customer 360."""

    tenant_id: UUID
    customer_id: UUID
    primary_contact_id: UUID | None
    primary_site_id: UUID | None
    contacts: tuple[Customer360ContactItem, ...]
    sites: tuple[Customer360SiteItem, ...]


class Customer360ContactsSitesService:
    """Compose CRM-owned contacts and sites without creating new aggregates."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        contacts: list[Contact] | tuple[Contact, ...] = (),
        sites: list[CustomerSite] | tuple[CustomerSite, ...] = (),
        request_context: RequestContext | None = None,
    ) -> Customer360ContactsSitesSection:
        Customer360ContactsSitesService._require_access(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )
        customer_contacts = tuple(
            item for item in contacts
            if item.tenant_id == tenant_id and item.customer_id == customer_id
        )
        customer_sites = tuple(
            item for item in sites
            if item.tenant_id == tenant_id and item.customer_id == customer_id
        )
        customer_contacts = tuple(sorted(customer_contacts, key=lambda item: (not item.is_primary, item.full_name.lower(), str(item.id))))
        customer_sites = tuple(sorted(customer_sites, key=lambda item: (not item.is_primary, item.name.lower(), str(item.id))))
        primary_contacts = [item for item in customer_contacts if item.is_primary and item.status is ContactStatus.ACTIVE]
        primary_sites = [item for item in customer_sites if item.is_primary and item.status is CustomerSiteStatus.ACTIVE]
        return Customer360ContactsSitesSection(
            tenant_id=tenant_id,
            customer_id=customer_id,
            primary_contact_id=primary_contacts[0].id if primary_contacts else None,
            primary_site_id=primary_sites[0].id if primary_sites else None,
            contacts=tuple(Customer360ContactsSitesService._contact_item(item) for item in customer_contacts),
            sites=tuple(Customer360ContactsSitesService._site_item(item) for item in customer_sites),
        )

    @staticmethod
    def _contact_item(item: Contact) -> Customer360ContactItem:
        return Customer360ContactItem(
            contact_id=item.id,
            full_name=item.full_name,
            job_title=item.job_title,
            email=item.email,
            phone=item.phone,
            mobile=item.mobile,
            status=item.status,
            primary=item.is_primary,
        )

    @staticmethod
    def _site_item(item: CustomerSite) -> Customer360SiteItem:
        return Customer360SiteItem(
            site_id=item.id,
            name=item.name,
            address_line_1=item.address_line_1,
            address_line_2=item.address_line_2,
            city=item.city,
            province=item.state_province,
            postal_code=item.postal_code,
            country=item.country,
            status=item.status,
            primary=item.is_primary,
        )

    @staticmethod
    def _require_access(*, tenant_id: UUID, customer_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
