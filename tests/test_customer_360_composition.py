from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Customer
from phoenix_crm.services import (
    Customer360CompositionService,
    Customer360ContactsSitesSection,
    Customer360DocumentsSection,
    Customer360Overview,
    Customer360PotentialSection,
    Customer360ProjectSiteSection,
    Customer360PurchaseSection,
    Customer360Reference,
    Customer360Timeline,
    Customer360View,
)


def make_customer(tenant_id=None):
    return Customer(
        tenant_id=tenant_id or uuid4(),
        name="Acme",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_sections(customer):
    view = Customer360View.from_customer(customer)
    overview = Customer360Overview(view, 1, 0, 0, 0, 0, 0, None)
    timeline = Customer360Timeline(customer.tenant_id, customer.id, ())
    purchases = Customer360PurchaseSection(
        customer.tenant_id, customer.id, False, 0, 0, None, None, (), (), "unavailable"
    )
    potential = Customer360PotentialSection(customer.tenant_id, customer.id, 0, 0, 0, (), (), ())
    contacts_sites = Customer360ContactsSitesSection(customer.tenant_id, customer.id, None, None, (), ())
    projects_sites = Customer360ProjectSiteSection(customer.tenant_id, customer.id, (), (), ())
    documents = Customer360DocumentsSection(customer.tenant_id, customer.id, False, ())
    return view, overview, timeline, purchases, potential, contacts_sites, projects_sites, documents


def test_composition_builds_complete_read_model():
    customer = make_customer()
    sections = make_sections(customer)
    result = Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])
    assert result.customer_id == customer.id
    assert result.tenant_id == customer.tenant_id
    assert result.overview is sections[1]
    assert result.timeline is sections[2]
    assert result.purchases is sections[3]
    assert result.potential is sections[4]
    assert result.contacts_sites is sections[5]
    assert result.projects_sites is sections[6]
    assert result.documents is sections[7]


def test_composition_rejects_mismatched_customer_view():
    customer = make_customer()
    other = make_customer(customer.tenant_id)
    sections = make_sections(other)
    with pytest.raises(ValueError):
        Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])


def test_composition_rejects_mismatched_section():
    customer = make_customer()
    sections = make_sections(customer)
    other = make_customer(customer.tenant_id)
    bad = Customer360Timeline(other.tenant_id, other.id, ())
    with pytest.raises(ValueError):
        Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=bad, purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])


def test_composition_enforces_core_access_scope():
    customer = make_customer()
    sections = make_sections(customer)
    context = RequestContext(TenantContext(str(customer.tenant_id)), UserContext(str(uuid4())), AccessScopeContext(resource_ids=frozenset({str(uuid4())})))
    with pytest.raises(PermissionError):
        Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7], request_context=context)


def test_composition_accepts_optional_sections_as_empty_unavailable_projections():
    customer = make_customer()
    sections = make_sections(customer)
    result = Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])
    assert result.purchases.available is False
    assert result.projects_sites.projects == ()
    assert result.documents.available is False


def test_composition_is_immutable():
    customer = make_customer()
    sections = make_sections(customer)
    result = Customer360CompositionService.build(customer=customer, view=sections[0], overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])
    with pytest.raises(AttributeError):
        result.customer_id = uuid4()


def test_composition_preserves_cross_module_references_without_importing_implementations():
    customer = make_customer()
    reference = Customer360Reference("sales", "opportunity", uuid4(), "Opportunity", "open")
    view = Customer360View.from_customer(customer, references=(reference,))
    sections = make_sections(customer)
    result = Customer360CompositionService.build(customer=customer, view=view, overview=sections[1], timeline=sections[2], purchases=sections[3], potential=sections[4], contacts_sites=sections[5], projects_sites=sections[6], documents=sections[7])
    assert result.view.references == (reference,)
