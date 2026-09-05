from datetime import timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import (
    CallCadence,
    Customer,
    CustomerCallClass,
    CustomerStatus,
    CustomerType,
)


def test_customer_type_is_configurable():
    customer_type = CustomerType(uuid4(), "Plumber", "PLUMBER")

    assert customer_type.name == "Plumber"
    assert customer_type.code == "PLUMBER"
    assert customer_type.active is True


def test_call_class_is_independent_from_customer_type():
    customer_type = CustomerType(uuid4(), "Plumber", "PLUMBER")
    call_class = CustomerCallClass(uuid4(), "Class A", "A", CallCadence(7))

    customer = Customer(uuid4(), "Example Customer", customer_type.id, call_class.id)

    assert customer.customer_type_id == customer_type.id
    assert customer.call_class_id == call_class.id
    assert call_class.cadence.interval_days == 7


def test_as_required_cadence_has_no_fixed_interval():
    cadence = CallCadence(None)

    assert cadence.interval_days is None


def test_customer_defaults_to_active():
    customer = Customer(uuid4(), "Example Customer", uuid4(), uuid4())

    assert customer.status is CustomerStatus.ACTIVE
    assert customer.id is not None
    assert customer.created_at.tzinfo is timezone.utc


def test_customer_rejects_empty_name():
    with pytest.raises(ValueError, match="Customer name cannot be empty"):
        Customer(uuid4(), "   ", uuid4(), uuid4())


def test_customer_type_rejects_empty_name():
    with pytest.raises(ValueError, match="Customer type name cannot be empty"):
        CustomerType(uuid4(), " ", "PLUMBER")


def test_call_class_rejects_non_positive_cadence():
    with pytest.raises(ValueError, match="Call cadence interval must be positive"):
        CallCadence(0)


def test_customer_rename_updates_timestamp():
    customer = Customer(uuid4(), "Old Name", uuid4(), uuid4())
    original_timestamp = customer.updated_at

    customer.rename("New Name")

    assert customer.name == "New Name"
    assert customer.updated_at >= original_timestamp


def test_customer_rename_rejects_empty_name():
    customer = Customer(uuid4(), "Customer", uuid4(), uuid4())

    with pytest.raises(ValueError, match="Customer name cannot be empty"):
        customer.rename(" ")
