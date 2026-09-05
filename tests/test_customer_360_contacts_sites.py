from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Contact, ContactStatus, CustomerSite, CustomerSiteStatus
from phoenix_crm.services import Customer360ContactsSitesService


def context(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_build_projects_primary_active_contact_and_site():
    tenant_id, customer_id = uuid4(), uuid4()
    contact = Contact(tenant_id, customer_id, "Jane", "Smith", is_primary=True, email="jane@example.com")
    site = CustomerSite(tenant_id, customer_id, "Head Office", is_primary=True, city="Johannesburg")
    section = Customer360ContactsSitesService.build(
        tenant_id=tenant_id, customer_id=customer_id, contacts=(contact,), sites=(site,)
    )
    assert section.primary_contact_id == contact.id
    assert section.primary_site_id == site.id
    assert section.contacts[0].full_name == "Jane Smith"
    assert section.sites[0].city == "Johannesburg"


def test_build_filters_other_tenant_and_customer_records():
    tenant_id, customer_id = uuid4(), uuid4()
    valid_contact = Contact(tenant_id, customer_id, "Valid", "Contact")
    other_tenant = Contact(uuid4(), customer_id, "Other", "Tenant")
    other_customer = Contact(tenant_id, uuid4(), "Other", "Customer")
    valid_site = CustomerSite(tenant_id, customer_id, "Valid Site")
    other_site = CustomerSite(uuid4(), customer_id, "Other Tenant Site")
    section = Customer360ContactsSitesService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        contacts=(valid_contact, other_tenant, other_customer),
        sites=(valid_site, other_site),
    )
    assert [item.full_name for item in section.contacts] == ["Valid Contact"]
    assert [item.name for item in section.sites] == ["Valid Site"]


def test_build_enforces_core_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(PermissionError):
        Customer360ContactsSitesService.build(
            tenant_id=tenant_id, customer_id=customer_id,
            request_context=context(tenant_id, uuid4()),
        )


def test_build_does_not_select_inactive_primary_as_primary():
    tenant_id, customer_id = uuid4(), uuid4()
    contact = Contact(tenant_id, customer_id, "Inactive", "Person", is_primary=True, status=ContactStatus.INACTIVE)
    site = CustomerSite(tenant_id, customer_id, "Closed Site", is_primary=True, status=CustomerSiteStatus.CLOSED)
    section = Customer360ContactsSitesService.build(
        tenant_id=tenant_id, customer_id=customer_id, contacts=(contact,), sites=(site,)
    )
    assert section.primary_contact_id is None
    assert section.primary_site_id is None


def test_build_orders_primary_items_first_then_display_name():
    tenant_id, customer_id = uuid4(), uuid4()
    contact_a = Contact(tenant_id, customer_id, "Zed", "Zulu")
    contact_b = Contact(tenant_id, customer_id, "Amy", "Alpha", is_primary=True)
    site_a = CustomerSite(tenant_id, customer_id, "Zulu Site")
    site_b = CustomerSite(tenant_id, customer_id, "Alpha Site", is_primary=True)
    section = Customer360ContactsSitesService.build(
        tenant_id=tenant_id, customer_id=customer_id,
        contacts=(contact_a, contact_b), sites=(site_a, site_b),
    )
    assert [item.full_name for item in section.contacts] == ["Amy Alpha", "Zed Zulu"]
    assert [item.name for item in section.sites] == ["Alpha Site", "Zulu Site"]


def test_build_is_read_only_for_domain_objects():
    tenant_id, customer_id = uuid4(), uuid4()
    contact = Contact(tenant_id, customer_id, "Jane", "Smith", is_primary=True)
    site = CustomerSite(tenant_id, customer_id, "Office", is_primary=True)
    original_contact_primary = contact.is_primary
    original_site_primary = site.is_primary
    Customer360ContactsSitesService.build(
        tenant_id=tenant_id, customer_id=customer_id, contacts=(contact,), sites=(site,)
    )
    assert contact.is_primary is original_contact_primary
    assert site.is_primary is original_site_primary
