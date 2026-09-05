"""Phase 12 activity-history tenant and Core access boundary tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ActivityType, CustomerActivity
from phoenix_crm.services.activity_service import ActivityService
from phoenix_crm.services.activity_timeline import ActivityTimelineService


def ctx(tenant_id, *resource_ids):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset(str(item) for item in resource_ids)),
    )


def activity(tenant_id, *, customer_id=None, contact_id=None, site_id=None, site_party_id=None):
    return CustomerActivity(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activity_type=ActivityType.CALL,
        subject="Boundary test",
        occurred_at=datetime.now(timezone.utc),
        contact_id=contact_id,
        site_id=site_id,
        site_party_id=site_party_id,
    )


def test_customer_history_filters_by_explicit_tenant():
    tenant = uuid4()
    other_tenant = uuid4()
    customer_id = uuid4()
    visible = activity(tenant, customer_id=customer_id)
    foreign = activity(other_tenant, customer_id=customer_id)
    result = ActivityService.history_for_customer(customer_id, [visible, foreign], tenant_id=tenant)
    assert result == (visible,)


def test_customer_history_rejects_context_tenant_mismatch():
    tenant = uuid4()
    customer_id = uuid4()
    with pytest.raises(PermissionError, match="tenant"):
        ActivityService.history_for_customer(
            customer_id,
            [],
            tenant_id=tenant,
            request_context=ctx(uuid4(), customer_id),
        )


def test_customer_history_rejects_resource_outside_context_scope():
    tenant = uuid4()
    with pytest.raises(PermissionError, match="resource"):
        ActivityService.history_for_customer(uuid4(), [], request_context=ctx(tenant))


def test_contact_history_filters_by_explicit_tenant():
    tenant = uuid4()
    other_tenant = uuid4()
    contact_id = uuid4()
    visible = activity(tenant, contact_id=contact_id)
    foreign = activity(other_tenant, contact_id=contact_id)
    result = ActivityService.history_for_contact(contact_id, [visible, foreign], tenant_id=tenant)
    assert result == (visible,)


def test_timeline_customer_history_enforces_core_resource_scope():
    tenant = uuid4()
    customer_id = uuid4()
    item = activity(tenant, customer_id=customer_id)
    with pytest.raises(PermissionError, match="resource"):
        ActivityTimelineService.for_customer(customer_id, [item], request_context=ctx(tenant))


def test_timeline_customer_history_filters_foreign_tenant():
    tenant = uuid4()
    other_tenant = uuid4()
    customer_id = uuid4()
    visible = activity(tenant, customer_id=customer_id)
    foreign = activity(other_tenant, customer_id=customer_id)
    result = ActivityTimelineService.for_customer(
        customer_id,
        [visible, foreign],
        tenant_id=tenant,
    )
    assert tuple(entry.activity for entry in result) == (visible,)


def test_timeline_contact_history_enforces_core_resource_scope():
    tenant = uuid4()
    contact_id = uuid4()
    with pytest.raises(PermissionError, match="resource"):
        ActivityTimelineService.for_contact(contact_id, [], request_context=ctx(tenant))


def test_timeline_site_history_enforces_core_resource_scope():
    tenant = uuid4()
    site_id = uuid4()
    with pytest.raises(PermissionError, match="resource"):
        ActivityTimelineService.for_site(site_id, [], request_context=ctx(tenant))


def test_timeline_site_party_history_enforces_core_resource_scope():
    tenant = uuid4()
    site_party_id = uuid4()
    with pytest.raises(PermissionError, match="resource"):
        ActivityTimelineService.for_site_party(site_party_id, [], request_context=ctx(tenant))
