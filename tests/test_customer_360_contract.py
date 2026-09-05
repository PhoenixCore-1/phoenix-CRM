from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import (
    CallCadence,
    Customer,
    CustomerCallClass,
    CustomerStatus,
)
from phoenix_crm.services import Customer360Reference, Customer360View


def make_customer():
    tenant_id = uuid4()
    customer = Customer(
        tenant_id=tenant_id,
        name="  Example Customer  ",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )
    return customer


def test_customer_360_view_projects_customer_identity():
    customer = make_customer()
    view = Customer360View.from_customer(customer)

    assert view.tenant_id == customer.tenant_id
    assert view.customer_id == customer.id
    assert view.customer_name == "Example Customer"
    assert view.customer_status is CustomerStatus.ACTIVE
    assert view.customer_type_id == customer.customer_type_id
    assert view.call_class_id == customer.call_class_id


def test_customer_360_view_copies_contact_and_site_relationship_ids_deterministically():
    customer = make_customer()
    contact_ids = [uuid4(), uuid4()]
    site_ids = [uuid4(), uuid4()]
    for contact_id in contact_ids:
        customer.add_contact(contact_id)
    for site_id in site_ids:
        customer.add_site(site_id)

    view = Customer360View.from_customer(customer)

    assert view.contact_ids == tuple(sorted(contact_ids, key=str))
    assert view.site_ids == tuple(sorted(site_ids, key=str))


def test_customer_360_view_is_immutable():
    customer = make_customer()
    view = Customer360View.from_customer(customer)

    with pytest.raises(AttributeError):
        view.customer_name = "Changed"


def test_customer_360_view_does_not_mutate_customer():
    customer = make_customer()
    customer.add_contact(uuid4())
    before = (customer.name, customer.contact_ids.copy(), customer.site_ids.copy())

    Customer360View.from_customer(customer)

    assert customer.name == before[0]
    assert customer.contact_ids == before[1]
    assert customer.site_ids == before[2]


def test_customer_360_view_accepts_relationship_and_interaction_context():
    customer = make_customer()
    last = datetime(2026, 9, 1, tzinfo=timezone.utc)
    next_interaction = datetime(2026, 9, 8, tzinfo=timezone.utc)
    reference = Customer360Reference(
        module_code="projects",
        resource_type="project",
        resource_id=uuid4(),
        label="Project Alpha",
        status="active",
    )

    view = Customer360View.from_customer(
        customer,
        primary_contact_id=uuid4(),
        last_interaction_at=last,
        next_interaction_at=next_interaction,
        relationship_health="healthy",
        references=(reference,),
    )

    assert view.last_interaction_at == last
    assert view.next_interaction_at == next_interaction
    assert view.relationship_health == "healthy"
    assert view.references == (reference,)


def test_customer_360_reference_requires_module_and_resource_type():
    with pytest.raises(ValueError):
        Customer360Reference(module_code="", resource_type="project", resource_id=uuid4())
    with pytest.raises(ValueError):
        Customer360Reference(module_code="projects", resource_type="", resource_id=uuid4())


def test_customer_360_reference_is_immutable():
    reference = Customer360Reference(
        module_code="projects",
        resource_type="project",
        resource_id=uuid4(),
    )

    with pytest.raises(AttributeError):
        reference.module_code = "sales"


def test_customer_360_contract_does_not_require_other_module_implementations():
    customer = make_customer()
    reference = Customer360Reference(
        module_code="sales",
        resource_type="opportunity",
        resource_id=uuid4(),
    )

    view = Customer360View.from_customer(customer, references=(reference,))

    assert view.references[0].module_code == "sales"
    assert view.references[0].resource_type == "opportunity"
