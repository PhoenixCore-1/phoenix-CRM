"""Phase 12 reporting, audit, and tenant/access hardening tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ActivityType, Customer, CustomerActivity, CustomerFollowUp, CustomerStatus, FollowUpStatus
from phoenix_crm.services import CRMAuditService, CRMReportingService


def ctx(tenant_id, user_id, *resource_ids):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset(str(item) for item in resource_ids)),
    )


def test_reporting_is_tenant_and_access_scoped():
    tenant = uuid4()
    other_tenant = uuid4()
    customer = Customer(tenant, "Visible", uuid4(), uuid4())
    hidden = Customer(tenant, "Hidden", uuid4(), uuid4())
    foreign = Customer(other_tenant, "Foreign", uuid4(), uuid4())
    result = CRMReportingService.build(
        tenant_id=tenant,
        reference_at=datetime.now(timezone.utc),
        customers=[customer, hidden, foreign],
        request_context=ctx(tenant, uuid4(), customer.id),
    )
    assert result.total_customers == 1
    assert result.active_customers == 1


def test_reporting_rejects_wrong_tenant_context():
    tenant = uuid4()
    with pytest.raises(PermissionError):
        CRMReportingService.build(
            tenant_id=tenant,
            reference_at=datetime.now(timezone.utc),
            request_context=ctx(uuid4(), uuid4()),
        )


def test_reporting_counts_open_overdue_and_recent_activity_deterministically():
    tenant = uuid4()
    customer = Customer(tenant, "Acme", uuid4(), uuid4())
    now = datetime.now(timezone.utc)
    open_due = CustomerFollowUp(tenant, customer.id, uuid4(), now - timedelta(days=1), "Call", status=FollowUpStatus.DUE)
    completed = CustomerFollowUp(tenant, customer.id, uuid4(), now - timedelta(days=2), "Done", status=FollowUpStatus.COMPLETED)
    recent = CustomerActivity(tenant, customer.id, ActivityType.CALL, "Recent", now - timedelta(days=2))
    old = CustomerActivity(tenant, customer.id, ActivityType.CALL, "Old", now - timedelta(days=60))
    result = CRMReportingService.build(
        tenant_id=tenant,
        reference_at=now,
        customers=[customer],
        follow_ups=[open_due, completed],
        activities=[recent, old],
    )
    assert result.open_follow_ups == 1
    assert result.overdue_follow_ups == 1
    assert result.recent_activities == 1


def test_reporting_rejects_non_positive_activity_window():
    with pytest.raises(ValueError, match="recent_activity_days"):
        CRMReportingService.build(tenant_id=uuid4(), reference_at=datetime.now(timezone.utc), recent_activity_days=0)


def test_audit_event_is_immutable_and_copies_metadata():
    metadata = {"source": "test"}
    event = CRMAuditService.record(
        tenant_id=uuid4(), actor_user_id=uuid4(), action="customer.updated", resource_type="customer", resource_id=uuid4(), metadata=metadata
    )
    metadata["source"] = "changed"
    assert event.metadata["source"] == "test"
    with pytest.raises(TypeError):
        event.metadata["x"] = "y"  # type: ignore[index]


def test_audit_requires_action_and_resource_type():
    with pytest.raises(ValueError, match="action"):
        CRMAuditService.record(tenant_id=uuid4(), actor_user_id=None, action=" ", resource_type="customer")
    with pytest.raises(ValueError, match="resource_type"):
        CRMAuditService.record(tenant_id=uuid4(), actor_user_id=None, action="read", resource_type=" ")


def test_audit_preserves_correlation_and_actor():
    tenant = uuid4()
    user = uuid4()
    resource = uuid4()
    event = CRMAuditService.record(
        tenant_id=tenant, actor_user_id=user, action="customer.viewed", resource_type="customer", resource_id=resource, correlation_id=" corr-1 "
    )
    assert event.tenant_id == tenant
    assert event.actor_user_id == user
    assert event.resource_id == resource
    assert event.correlation_id == "corr-1"


def test_closed_customer_is_not_counted_as_active():
    tenant = uuid4()
    customer = Customer(tenant, "Closed", uuid4(), uuid4(), status=CustomerStatus.CLOSED)
    result = CRMReportingService.build(tenant_id=tenant, reference_at=datetime.now(timezone.utc), customers=[customer])
    assert result.total_customers == 1
    assert result.active_customers == 0
    assert result.closed_customers == 1
