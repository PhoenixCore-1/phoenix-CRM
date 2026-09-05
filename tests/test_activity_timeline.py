"""Tests for Phase 4.4 relationship activity timeline."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from phoenix_crm.domain import ActivityType, CustomerActivity
from phoenix_crm.services import ActivityTimelineService


def make_activity(*, customer_id=None, contact_id=None, site_id=None, site_party_id=None, occurred_at=None):
    return CustomerActivity(
        tenant_id=uuid4(),
        customer_id=customer_id or uuid4(),
        activity_type=ActivityType.CALL,
        subject="Relationship review",
        occurred_at=occurred_at or datetime.now(timezone.utc),
        contact_id=contact_id,
        site_id=site_id,
        site_party_id=site_party_id,
    )


def test_customer_timeline_is_newest_first_and_context_rich():
    customer_id = uuid4()
    older = make_activity(customer_id=customer_id, occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc))
    newer = make_activity(
        customer_id=customer_id,
        contact_id=uuid4(),
        site_id=uuid4(),
        occurred_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    entries = ActivityTimelineService.for_customer(customer_id, [older, newer])
    assert [entry.activity.id for entry in entries] == [newer.id, older.id]
    assert entries[0].has_relationship_context is True


def test_customer_timeline_supports_date_filters():
    customer_id = uuid4()
    first = make_activity(customer_id=customer_id, occurred_at=datetime(2026, 9, 1, tzinfo=timezone.utc))
    second = make_activity(customer_id=customer_id, occurred_at=datetime(2026, 9, 5, tzinfo=timezone.utc))
    third = make_activity(customer_id=customer_id, occurred_at=datetime(2026, 9, 10, tzinfo=timezone.utc))
    entries = ActivityTimelineService.for_customer(
        customer_id,
        [first, second, third],
        after=datetime(2026, 9, 5, tzinfo=timezone.utc),
        before=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )
    assert [entry.activity.id for entry in entries] == [second.id]


def test_contact_timeline_only_returns_matching_contact():
    contact_id = uuid4()
    matching = make_activity(contact_id=contact_id)
    other = make_activity(contact_id=uuid4())
    entries = ActivityTimelineService.for_contact(contact_id, [other, matching])
    assert [entry.activity.id for entry in entries] == [matching.id]


def test_site_timeline_returns_site_relationship_activities():
    site_id = uuid4()
    matching = make_activity(site_id=site_id)
    other = make_activity(site_id=uuid4())
    entries = ActivityTimelineService.for_site(site_id, [other, matching])
    assert [entry.activity.id for entry in entries] == [matching.id]
    assert entries[0].site_id == site_id


def test_site_party_timeline_returns_party_relationship_activities():
    site_party_id = uuid4()
    matching = make_activity(site_party_id=site_party_id)
    entries = ActivityTimelineService.for_site_party(site_party_id, [matching])
    assert entries[0].site_party_id == site_party_id


def test_timeline_entry_without_relationship_context_is_supported():
    activity = make_activity()
    entry = ActivityTimelineService.for_customer(activity.customer_id, [activity])[0]
    assert entry.has_relationship_context is False


def test_customer_timeline_excludes_other_customers():
    customer_id = uuid4()
    matching = make_activity(customer_id=customer_id)
    other = make_activity(customer_id=uuid4())
    entries = ActivityTimelineService.for_customer(customer_id, [other, matching])
    assert len(entries) == 1
    assert entries[0].customer_id == customer_id


def test_same_timestamp_order_is_deterministic():
    customer_id = uuid4()
    occurred_at = datetime(2026, 9, 5, tzinfo=timezone.utc)
    first = make_activity(customer_id=customer_id, occurred_at=occurred_at)
    second = make_activity(customer_id=customer_id, occurred_at=occurred_at)
    entries = ActivityTimelineService.for_customer(customer_id, [first, second])
    expected = sorted([first.id, second.id], key=str, reverse=True)
    assert [entry.activity.id for entry in entries] == expected
