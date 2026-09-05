"""Tests for Phase 5.4 call cadence engine."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import (
    ActivityType,
    CallCadence,
    Customer,
    CustomerActivity,
    CustomerCallClass,
)
from phoenix_crm.services import CallCadenceService


REFERENCE = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)


def make_customer(*, call_class_id=None, tenant_id=None):
    return Customer(
        tenant_id=tenant_id or uuid4(),
        name="Acme",
        customer_type_id=uuid4(),
        call_class_id=call_class_id or uuid4(),
    )


def make_class(customer, *, days=7):
    return CustomerCallClass(
        id=customer.call_class_id,
        name="A Weekly",
        code="A",
        cadence=CallCadence(days),
    )


def make_activity(customer, occurred_at):
    return CustomerActivity(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Customer call",
        occurred_at=occurred_at,
    )


def test_next_interaction_uses_configured_interval():
    call_class = CustomerCallClass(uuid4(), "B", "B", CallCadence(14))
    last = datetime(2026, 9, 1, 9, tzinfo=timezone.utc)
    assert CallCadenceService.next_interaction_at(last, call_class) == last + timedelta(days=14)


def test_next_interaction_uses_reference_when_no_previous_interaction():
    call_class = CustomerCallClass(uuid4(), "C", "C", CallCadence(28))
    assert CallCadenceService.next_interaction_at(None, call_class, reference_at=REFERENCE) == REFERENCE + timedelta(days=28)


def test_unconfigured_cadence_returns_no_next_date():
    call_class = CustomerCallClass(uuid4(), "E", "E", CallCadence(None))
    assert CallCadenceService.next_interaction_at(REFERENCE, call_class) is None


def test_resolve_uses_latest_customer_activity():
    customer = make_customer()
    call_class = make_class(customer, days=14)
    older = make_activity(customer, REFERENCE - timedelta(days=10))
    latest = make_activity(customer, REFERENCE - timedelta(days=2))
    result = CallCadenceService.resolve(customer, call_class, [older, latest])
    assert result.last_interaction_at == latest.occurred_at
    assert result.next_interaction_at == latest.occurred_at + timedelta(days=14)
    assert result.interval_days == 14


def test_resolve_ignores_other_customer_activities():
    customer = make_customer()
    call_class = make_class(customer)
    other = make_customer(tenant_id=customer.tenant_id)
    result = CallCadenceService.resolve(
        customer,
        call_class,
        [make_activity(other, REFERENCE)],
        reference_at=REFERENCE,
    )
    assert result.last_interaction_at is None
    assert result.next_interaction_at == REFERENCE + timedelta(days=7)


def test_resolve_ignores_cross_tenant_activities():
    customer = make_customer()
    call_class = make_class(customer)
    foreign = make_customer()
    result = CallCadenceService.resolve(customer, call_class, [make_activity(foreign, REFERENCE)])
    assert result.last_interaction_at is None


def test_resolve_without_activity_uses_reference_time():
    customer = make_customer()
    call_class = make_class(customer, days=7)
    result = CallCadenceService.resolve(customer, call_class, [], reference_at=REFERENCE)
    assert result.last_interaction_at is None
    assert result.next_interaction_at == REFERENCE + timedelta(days=7)


def test_resolve_rejects_wrong_call_class():
    customer = make_customer()
    wrong_class = CustomerCallClass(uuid4(), "B", "B", CallCadence(14))
    with pytest.raises(ValueError, match="does not match"):
        CallCadenceService.resolve(customer, wrong_class, [])


def test_last_interaction_returns_latest_timestamp():
    customer = make_customer()
    first = make_activity(customer, REFERENCE - timedelta(days=5))
    latest = make_activity(customer, REFERENCE - timedelta(days=1))
    assert CallCadenceService.last_interaction(customer.id, [first, latest]) == latest.occurred_at
