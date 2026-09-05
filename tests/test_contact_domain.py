from datetime import timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import Contact, ContactStatus


def test_contact_defaults_to_active():
    contact = Contact(uuid4(), uuid4(), " Jane ", " Doe ")

    assert contact.first_name == "Jane"
    assert contact.last_name == "Doe"
    assert contact.full_name == "Jane Doe"
    assert contact.status is ContactStatus.ACTIVE
    assert contact.created_at.tzinfo is timezone.utc


def test_contact_is_linked_to_customer_and_tenant():
    tenant_id = uuid4()
    customer_id = uuid4()
    contact = Contact(tenant_id, customer_id, "Jane", "Doe")

    assert contact.tenant_id == tenant_id
    assert contact.customer_id == customer_id


def test_contact_supports_business_contact_details():
    contact = Contact(
        uuid4(),
        uuid4(),
        "Jane",
        "Doe",
        job_title="Purchasing Manager",
        email=" jane@example.com ",
        phone="011 555 1234",
        mobile="082 555 5678",
    )

    assert contact.job_title == "Purchasing Manager"
    assert contact.email == "jane@example.com"
    assert contact.phone == "011 555 1234"
    assert contact.mobile == "082 555 5678"


def test_contact_can_be_primary():
    contact = Contact(uuid4(), uuid4(), "Jane", "Doe")
    original_timestamp = contact.updated_at

    contact.set_primary(True)

    assert contact.is_primary is True
    assert contact.updated_at >= original_timestamp


def test_contact_rename_updates_name_and_timestamp():
    contact = Contact(uuid4(), uuid4(), "Jane", "Doe")
    original_timestamp = contact.updated_at

    contact.rename("John", "Smith")

    assert contact.full_name == "John Smith"
    assert contact.updated_at >= original_timestamp


def test_contact_rejects_empty_first_name():
    with pytest.raises(ValueError, match="Contact first name cannot be empty"):
        Contact(uuid4(), uuid4(), " ", "Doe")


def test_contact_rejects_empty_last_name():
    with pytest.raises(ValueError, match="Contact last name cannot be empty"):
        Contact(uuid4(), uuid4(), "Jane", " ")
