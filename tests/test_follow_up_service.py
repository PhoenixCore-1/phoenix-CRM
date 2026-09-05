"""Tests for Phase 5.2 follow-up service and lifecycle."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import Customer, CustomerFollowUp, FollowUpStatus
from phoenix_crm.services import FollowUpService


def make_customer(*, tenant_id=None) -> Customer:
    return Customer(
        tenant_id=tenant_id or uuid4(),
        name="Acme Customer",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_follow_up(customer: Customer, *, due_at=None, user_id=None) -> CustomerFollowUp:
    return CustomerFollowUp(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=user_id or uuid4(),
        due_at=due_at or datetime(2026, 9, 10, 10, tzinfo=timezone.utc),
        reason="Confirm requirements",
    )


def test_record_follow_up_accepts_matching_customer():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    assert FollowUpService.record_follow_up(follow_up, customer) is follow_up


def test_record_follow_up_rejects_cross_tenant():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    follow_up.tenant_id = uuid4()
    with pytest.raises(ValueError, match="same tenant"):
        FollowUpService.record_follow_up(follow_up, customer)


def test_record_follow_up_rejects_wrong_customer():
    customer = make_customer()
    other_customer = make_customer(tenant_id=customer.tenant_id)
    follow_up = make_follow_up(other_customer)
    with pytest.raises(ValueError, match="does not match"):
        FollowUpService.record_follow_up(follow_up, customer)


def test_complete_delegates_lifecycle_and_returns_follow_up():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    completed_at = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)
    result = FollowUpService.complete(follow_up, customer, completed_at=completed_at)
    assert result is follow_up
    assert follow_up.status is FollowUpStatus.COMPLETED
    assert follow_up.completed_at == completed_at


def test_cancel_delegates_lifecycle():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    assert FollowUpService.cancel(follow_up, customer) is follow_up
    assert follow_up.status is FollowUpStatus.CANCELLED


def test_reschedule_updates_due_date_and_status():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    new_due = datetime(2026, 9, 20, 9, tzinfo=timezone.utc)
    FollowUpService.reschedule(follow_up, customer, new_due)
    assert follow_up.due_at == new_due
    assert follow_up.status is FollowUpStatus.RESCHEDULED


def test_mark_due_updates_status():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    FollowUpService.mark_due(follow_up, customer)
    assert follow_up.status is FollowUpStatus.DUE


def test_customer_retrieval_filters_and_orders_by_due_date():
    customer = make_customer()
    first = make_follow_up(customer, due_at=datetime(2026, 9, 12, tzinfo=timezone.utc))
    second = make_follow_up(customer, due_at=datetime(2026, 9, 8, tzinfo=timezone.utc))
    other = make_follow_up(make_customer(), due_at=datetime(2026, 9, 20, tzinfo=timezone.utc))
    result = FollowUpService.for_customer(customer.id, [first, second, other])
    assert result == (first, second)


def test_customer_retrieval_can_scope_to_tenant():
    customer = make_customer()
    valid = make_follow_up(customer)
    foreign = make_follow_up(customer)
    foreign.tenant_id = uuid4()
    result = FollowUpService.for_customer(customer.id, [valid, foreign], tenant_id=customer.tenant_id)
    assert result == (valid,)


def test_user_retrieval_orders_earliest_due_first():
    customer = make_customer()
    user_id = uuid4()
    late = make_follow_up(
        customer,
        due_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        user_id=user_id,
    )
    early = make_follow_up(
        customer,
        due_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        user_id=user_id,
    )
    result = FollowUpService.assigned_to_user(user_id, [late, early])
    assert result == (early, late)


def test_user_retrieval_can_exclude_completed():
    customer = make_customer()
    user_id = uuid4()
    completed = make_follow_up(customer, user_id=user_id)
    completed.complete()
    active = make_follow_up(customer, due_at=datetime(2026, 9, 11, tzinfo=timezone.utc), user_id=user_id)
    result = FollowUpService.assigned_to_user(user_id, [completed, active], include_completed=False)
    assert result == (active,)


def test_user_retrieval_can_scope_to_tenant():
    customer = make_customer()
    user_id = uuid4()
    valid = make_follow_up(customer, user_id=user_id)
    foreign = make_follow_up(customer, user_id=user_id)
    foreign.tenant_id = uuid4()
    result = FollowUpService.assigned_to_user(user_id, [valid, foreign], tenant_id=customer.tenant_id)
    assert result == (valid,)
