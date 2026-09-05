from uuid import uuid4

from phoenix_crm.domain import Customer


def test_customer_can_associate_multiple_contacts():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    first_contact = uuid4()
    second_contact = uuid4()

    customer.add_contact(first_contact)
    customer.add_contact(second_contact)

    assert customer.contact_ids == {first_contact, second_contact}


def test_customer_can_remove_contact_association():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    contact_id = uuid4()

    customer.add_contact(contact_id)
    customer.remove_contact(contact_id)

    assert contact_id not in customer.contact_ids


def test_customer_can_associate_multiple_sites():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    first_site = uuid4()
    second_site = uuid4()

    customer.add_site(first_site)
    customer.add_site(second_site)

    assert customer.site_ids == {first_site, second_site}


def test_customer_can_remove_site_association():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    site_id = uuid4()

    customer.add_site(site_id)
    customer.remove_site(site_id)

    assert site_id not in customer.site_ids


def test_customer_relationship_changes_update_timestamp():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    original_timestamp = customer.updated_at
    contact_id = uuid4()

    customer.add_contact(contact_id)

    assert customer.updated_at >= original_timestamp


def test_customer_relationship_ids_are_independent_collections():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())
    contact_id = uuid4()
    site_id = uuid4()

    customer.add_contact(contact_id)
    customer.add_site(site_id)

    assert customer.contact_ids == {contact_id}
    assert customer.site_ids == {site_id}
