"""Tests for Phase 5.1 follow-up domain."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import CustomerFollowUp, FollowUpPriority, FollowUpStatus


def make_follow_up() -> CustomerFollowUp:
    return CustomerFollowUp(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        assigned_to_user_id=uuid4(),
        due_at=datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc),
        reason="Confirm project requirements",
        contact_id=uuid4(),
        site_id=uuid4(),
        site_party_id=uuid4(),
        related_activity_id=uuid4(),
        priority=FollowUpPriority.HIGH,
        notes="Customer requested a technical follow-up.",
    )


def test_follow_up_defaults_to_planned_and_stores_context():
    follow_up = make_follow_up()
    assert follow_up.status is FollowUpStatus.PLANNED
    assert follow_up.priority is FollowUpPriority.HIGH
    assert follow_up.contact_id is not None
    assert follow_up.site_id is not None
    assert follow_up.site_party_id is not None
    assert follow_up.related_activity_id is not None


def test_follow_up_requires_reason():
    with pytest.raises(ValueError, match="reason cannot be empty"):
        CustomerFollowUp(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            assigned_to_user_id=uuid4(),
            due_at=datetime.now(timezone.utc),
            reason="   ",
        )


def test_follow_up_strips_reason_and_notes():
    follow_up = CustomerFollowUp(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        assigned_to_user_id=uuid4(),
        due_at=datetime.now(timezone.utc),
        reason="  Call customer  ",
        notes="  Confirm availability  ",
    )
    assert follow_up.reason == "Call customer"
    assert follow_up.notes == "Confirm availability"


def test_complete_sets_status_and_timestamp():
    follow_up = make_follow_up()
    completed_at = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    follow_up.complete(completed_at=completed_at)
    assert follow_up.status is FollowUpStatus.COMPLETED
    assert follow_up.completed_at == completed_at


def test_cancel_sets_cancelled_status():
    follow_up = make_follow_up()
    follow_up.cancel()
    assert follow_up.status is FollowUpStatus.CANCELLED


def test_reschedule_updates_due_date_and_status():
    follow_up = make_follow_up()
    new_due = datetime(2026, 9, 15, 14, 0, tzinfo=timezone.utc)
    follow_up.reschedule(new_due)
    assert follow_up.due_at == new_due
    assert follow_up.status is FollowUpStatus.RESCHEDULED


def test_mark_due_sets_due_status():
    follow_up = make_follow_up()
    follow_up.mark_due()
    assert follow_up.status is FollowUpStatus.DUE


def test_completed_follow_up_cannot_be_completed_cancelled_or_rescheduled():
    follow_up = make_follow_up()
    follow_up.complete()
    with pytest.raises(ValueError):
        follow_up.complete()
    with pytest.raises(ValueError):
        follow_up.cancel()
    with pytest.raises(ValueError):
        follow_up.reschedule(datetime.now(timezone.utc))


def test_cancelled_follow_up_cannot_be_completed_cancelled_or_rescheduled():
    follow_up = make_follow_up()
    follow_up.cancel()
    with pytest.raises(ValueError):
        follow_up.complete()
    with pytest.raises(ValueError):
        follow_up.cancel()
    with pytest.raises(ValueError):
        follow_up.reschedule(datetime.now(timezone.utc))
