"""Tests for Phase 4.2 activity service and relationship history."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import ActivityType, Customer, CustomerActivity
from phoenix_crm.services.activity_service import ActivityService


def make_customer() -> Customer:
    return Customer(
        tenant_id=uuid4(),
        name="Acme Construction",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_activity(customer: Customer, *, occurred_at: datetime, contact_id=None) -> CustomerActivity:
    return CustomerActivity(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Relationship discussion",
        occurred_at=occurred_at,
        performed_by_user_id=uuid4(),
        contact_id=contact_id,
        notes="Relationship discussion",
    )


def test_record_activity_accepts_matching_customer():
    customer = make_customer()
    activity = make_activity(customer, occurred_at=datetime.now(timezone.utc))
    assert ActivityService.record_activity(activity, customer) is activity


def test_record_activity_rejects_cross_tenant_activity():
    customer = make_customer()
    activity = make_activity(customer, occurred_at=datetime.now(timezone.utc))
    activity.tenant_id = uuid4()
    with pytest.raises(ValueError, match="same tenant"):
        ActivityService.record_activity(activity, customer)


def test_record_activity_rejects_wrong_customer():
    customer = make_customer()
    activity = make_activity(customer, occurred_at=datetime.now(timezone.utc))
    activity.customer_id = uuid4()
    with pytest.raises(ValueError, match="does not match"):
        ActivityService.record_activity(activity, customer)


def test_history_returns_only_requested_customer():
    customer = make_customer()
    other = make_customer()
    first = make_activity(customer, occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    other_activity = make_activity(other, occurred_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
    history = ActivityService.history_for_customer(customer.id, [other_activity, first])
    assert history == (first,)


def test_history_is_newest_first():
    customer = make_customer()
    older = make_activity(customer, occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = make_activity(customer, occurred_at=datetime(2026, 1, 3, tzinfo=timezone.utc))
    history = ActivityService.history_for_customer(customer.id, [older, newer])
    assert history == (newer, older)


def test_history_supports_after_filter():
    customer = make_customer()
    start = datetime(2026, 1, 2, tzinfo=timezone.utc)
    older = make_activity(customer, occurred_at=start - timedelta(days=1))
    current = make_activity(customer, occurred_at=start)
    newer = make_activity(customer, occurred_at=start + timedelta(days=1))
    history = ActivityService.history_for_customer(customer.id, [older, current, newer], after=start)
    assert history == (newer, current)


def test_history_supports_before_filter():
    customer = make_customer()
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    older = make_activity(customer, occurred_at=end - timedelta(days=1))
    current = make_activity(customer, occurred_at=end)
    newer = make_activity(customer, occurred_at=end + timedelta(days=1))
    history = ActivityService.history_for_customer(customer.id, [older, current, newer], before=end)
    assert history == (current, older)


def test_contact_history_returns_matching_contact_only():
    customer = make_customer()
    contact_id = uuid4()
    matching = make_activity(
        customer,
        occurred_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        contact_id=contact_id,
    )
    other = make_activity(
        customer,
        occurred_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        contact_id=uuid4(),
    )
    history = ActivityService.history_for_contact(contact_id, [other, matching])
    assert history == (matching,)


def test_history_returns_empty_tuple_when_no_activities_match():
    customer = make_customer()
    assert ActivityService.history_for_customer(customer.id, []) == ()


def test_history_uses_activity_id_as_deterministic_tiebreaker():
    customer = make_customer()
    occurred = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = make_activity(customer, occurred_at=occurred)
    second = make_activity(customer, occurred_at=occurred)
    expected = tuple(sorted((first, second), key=lambda item: str(item.id), reverse=True))
    assert ActivityService.history_for_customer(customer.id, [first, second]) == expected
