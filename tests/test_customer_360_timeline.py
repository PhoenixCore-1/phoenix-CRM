from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ActivitySource, ActivityType, CustomerActivity, InteractionDirection
from phoenix_crm.services import Customer360TimelineService


def make_activity(tenant_id, customer_id, day, subject):
    return CustomerActivity(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activity_type=ActivityType.CALL,
        subject=subject,
        occurred_at=datetime(2026, 1, day, tzinfo=timezone.utc),
        direction=InteractionDirection.OUTBOUND,
        source=ActivitySource.MANUAL,
    )


def context_for(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_timeline_returns_newest_first():
    tenant_id, customer_id = uuid4(), uuid4()
    older = make_activity(tenant_id, customer_id, 1, "Older")
    newer = make_activity(tenant_id, customer_id, 2, "Newer")
    timeline = Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id, activities=[older, newer]
    )
    assert [entry.subject for entry in timeline.entries] == ["Newer", "Older"]


def test_timeline_maps_activity_metadata():
    tenant_id, customer_id = uuid4(), uuid4()
    activity = make_activity(tenant_id, customer_id, 1, "Call customer")
    timeline = Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id, activities=[activity]
    )
    entry = timeline.entries[0]
    assert entry.activity_id == activity.id
    assert entry.activity_type == ActivityType.CALL.value
    assert entry.direction == InteractionDirection.OUTBOUND.value
    assert entry.source == ActivitySource.MANUAL.value


def test_timeline_excludes_other_tenant_and_customer():
    tenant_id, customer_id = uuid4(), uuid4()
    records = [
        make_activity(tenant_id, customer_id, 1, "Included"),
        make_activity(uuid4(), customer_id, 2, "Other tenant"),
        make_activity(tenant_id, uuid4(), 3, "Other customer"),
    ]
    timeline = Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id, activities=records
    )
    assert [entry.subject for entry in timeline.entries] == ["Included"]


def test_timeline_enforces_core_tenant_and_customer_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(PermissionError):
        Customer360TimelineService.build(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=context_for(uuid4(), customer_id),
        )
    with pytest.raises(PermissionError):
        Customer360TimelineService.build(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=context_for(tenant_id, uuid4()),
        )


def test_timeline_limit_is_applied_after_ordering():
    tenant_id, customer_id = uuid4(), uuid4()
    activities = [make_activity(tenant_id, customer_id, day, str(day)) for day in range(1, 4)]
    timeline = Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id, activities=activities, limit=2
    )
    assert [entry.subject for entry in timeline.entries] == ["3", "2"]


def test_timeline_rejects_non_positive_limit():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(ValueError):
        Customer360TimelineService.build(
            tenant_id=tenant_id, customer_id=customer_id, limit=0
        )


def test_timeline_does_not_mutate_input_collection():
    tenant_id, customer_id = uuid4(), uuid4()
    first = make_activity(tenant_id, customer_id, 1, "First")
    second = make_activity(tenant_id, customer_id, 2, "Second")
    activities = [first, second]
    original = tuple(activities)
    Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id, activities=activities
    )
    assert tuple(activities) == original


def test_empty_timeline_is_supported():
    tenant_id, customer_id = uuid4(), uuid4()
    timeline = Customer360TimelineService.build(
        tenant_id=tenant_id, customer_id=customer_id
    )
    assert timeline.entries == ()
