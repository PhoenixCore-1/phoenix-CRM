"""Tests for Phase 4.1 and 4.3 customer activity domain."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import ActivityOutcome, ActivityType, CustomerActivity


def make_activity() -> CustomerActivity:
    return CustomerActivity(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        activity_type=ActivityType.CALL,
        subject="Quarterly account review",
        occurred_at=datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc),
        contact_id=uuid4(),
        performed_by_user_id=uuid4(),
        outcome=ActivityOutcome.POSITIVE,
        notes="Customer confirmed upcoming project requirements.",
    )


def test_activity_stores_customer_and_contact_context():
    activity = make_activity()
    assert activity.customer_id is not None
    assert activity.contact_id is not None
    assert activity.activity_type is ActivityType.CALL


def test_activity_strips_subject_and_notes():
    activity = CustomerActivity(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        activity_type=ActivityType.NOTE,
        subject="  Account note  ",
        occurred_at=datetime.now(timezone.utc),
        notes="  Important relationship detail  ",
    )
    assert activity.subject == "Account note"
    assert activity.notes == "Important relationship detail"


def test_activity_requires_subject():
    with pytest.raises(ValueError, match="subject cannot be empty"):
        CustomerActivity(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            activity_type=ActivityType.CALL,
            subject="   ",
            occurred_at=datetime.now(timezone.utc),
        )


def test_activity_supports_all_relationship_activity_types():
    for activity_type in ActivityType:
        activity = CustomerActivity(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            activity_type=activity_type,
            subject="Relationship interaction",
            occurred_at=datetime.now(timezone.utc),
        )
        assert activity.activity_type is activity_type


def test_update_details_changes_business_details():
    activity = make_activity()
    activity.update_details(
        subject="Updated account review",
        outcome=ActivityOutcome.FOLLOW_UP_REQUIRED,
        notes="Prepare technical proposal.",
    )
    assert activity.subject == "Updated account review"
    assert activity.outcome is ActivityOutcome.FOLLOW_UP_REQUIRED
    assert activity.notes == "Prepare technical proposal."


def test_update_details_rejects_empty_subject():
    activity = make_activity()
    with pytest.raises(ValueError, match="subject cannot be empty"):
        activity.update_details(subject="   ")


def test_update_details_preserves_occurred_at():
    activity = make_activity()
    occurred_at = activity.occurred_at
    activity.update_details(notes="Updated history")
    assert activity.occurred_at == occurred_at


def test_activity_supports_site_relationship_context():
    activity = make_activity()
    site_id = uuid4()
    activity.set_relationship_context(site_id=site_id)
    assert activity.site_id == site_id
    assert activity.contact_id is None
    assert activity.site_party_id is None


def test_activity_supports_site_party_relationship_context():
    activity = make_activity()
    site_party_id = uuid4()
    activity.set_relationship_context(site_party_id=site_party_id)
    assert activity.site_party_id == site_party_id
    assert activity.contact_id is None
    assert activity.site_id is None


def test_activity_supports_combined_relationship_context():
    activity = make_activity()
    contact_id = uuid4()
    site_id = uuid4()
    site_party_id = uuid4()
    activity.set_relationship_context(
        contact_id=contact_id,
        site_id=site_id,
        site_party_id=site_party_id,
    )
    assert activity.contact_id == contact_id
    assert activity.site_id == site_id
    assert activity.site_party_id == site_party_id


def test_activity_relationship_context_can_be_cleared():
    activity = make_activity()
    activity.set_relationship_context(
        contact_id=uuid4(),
        site_id=uuid4(),
        site_party_id=uuid4(),
    )
    activity.set_relationship_context()
    assert activity.contact_id is None
    assert activity.site_id is None
    assert activity.site_party_id is None
