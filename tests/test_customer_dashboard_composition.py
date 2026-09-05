"""Tests for Phase 10.5/10.6 CRM dashboard composition and hardening."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import CustomerStatus
from phoenix_crm.services import (
    CRMWorkItemType,
    CRMWorkQueueItem,
    CustomerDashboardCompositionService,
    CustomerDashboardKPIs,
)


def _kpis(tenant_id):
    return CustomerDashboardKPIs(
        tenant_id=tenant_id,
        total_customers=10,
        active_customers=7,
        prospect_customers=2,
        on_hold_customers=1,
        inactive_customers=0,
        closed_customers=0,
        new_leads=3,
        potential_customers=2,
        active_potential=4,
        open_follow_ups=5,
        overdue_follow_ups=1,
        calls_due=2,
        recent_activities=8,
        customers_by_type=(("Builder", 4),),
        customers_by_call_class=(("A", 10),),
    )


def _queue(tenant_id):
    customer_id = uuid4()
    user_id = uuid4()
    reference_at = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)
    return reference_at, (
        CRMWorkQueueItem(customer_id, "Acme", CRMWorkItemType.CALL, reference_at - timedelta(hours=1), assigned_to_user_id=user_id),
        CRMWorkQueueItem(customer_id, "Acme", CRMWorkItemType.FOLLOW_UP, reference_at + timedelta(days=1), follow_up_id=uuid4(), assigned_to_user_id=user_id),
    )


def test_composes_kpis_and_work_queue_into_one_read_model():
    tenant_id = uuid4()
    reference_at, queue = _queue(tenant_id)
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), work_queue=queue, reference_at=reference_at)
    assert result.tenant_id == tenant_id
    assert result.kpis.total_customers == 10
    assert result.work_queue == queue
    assert tuple(section.key for section in result.sections) == ("customers", "work_queue", "leads_and_potential", "work_queue_items")


def test_work_queue_section_has_deterministic_summary_metrics():
    tenant_id = uuid4()
    reference_at, queue = _queue(tenant_id)
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), work_queue=queue, reference_at=reference_at)
    metrics = {metric.key: metric.value for metric in result.sections[-1].metrics}
    assert metrics == {"total_work_items": 2, "due_or_overdue_work_items": 1, "overdue_work_items": 1, "call_work_items": 1, "follow_up_work_items": 1}


def test_empty_work_queue_is_graceful():
    tenant_id = uuid4()
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc))
    assert result.work_queue == ()
    metrics = {metric.key: metric.value for metric in result.sections[-1].metrics}
    assert metrics["total_work_items"] == 0
    assert metrics["due_or_overdue_work_items"] == 0
    assert metrics["overdue_work_items"] == 0


def test_kpi_tenant_mismatch_is_rejected():
    with pytest.raises(ValueError, match="tenant"):
        CustomerDashboardCompositionService.build(tenant_id=uuid4(), user_id=uuid4(), kpis=_kpis(uuid4()), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc))


def test_core_tenant_scope_is_enforced():
    tenant_id = uuid4()
    user_id = uuid4()
    context = RequestContext(tenant=TenantContext(str(uuid4())), user=UserContext(str(user_id)))
    with pytest.raises(PermissionError, match="tenant"):
        CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=user_id, kpis=_kpis(tenant_id), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc), request_context=context)


def test_core_matching_tenant_is_accepted():
    tenant_id = uuid4()
    user_id = uuid4()
    context = RequestContext(tenant=TenantContext(str(tenant_id)), user=UserContext(str(user_id)), access_scope=AccessScopeContext(resource_ids=frozenset()))
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=user_id, kpis=_kpis(tenant_id), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc), request_context=context)
    assert result.user_id == user_id


def test_composition_is_read_only():
    tenant_id = uuid4()
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc))
    with pytest.raises((AttributeError, TypeError)):
        result.sections = ()
    assert CustomerStatus.ACTIVE.value == "active"


def test_queue_is_filtered_to_core_resource_scope():
    tenant_id = uuid4()
    reference_at = datetime(2026, 9, 5, tzinfo=timezone.utc)
    allowed = uuid4()
    denied = uuid4()
    queue = (
        CRMWorkQueueItem(allowed, "Allowed", CRMWorkItemType.CALL, reference_at),
        CRMWorkQueueItem(denied, "Denied", CRMWorkItemType.CALL, reference_at),
    )
    context = RequestContext(tenant=TenantContext(str(tenant_id)), user=UserContext(str(uuid4())), access_scope=AccessScopeContext(resource_ids=frozenset({str(allowed)})))
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=UUID(context.user.user_id), kpis=_kpis(tenant_id), work_queue=queue, reference_at=reference_at, request_context=context)
    assert tuple(item.customer_id for item in result.work_queue) == (allowed,)


def test_queue_order_is_hardened_deterministically():
    tenant_id = uuid4()
    reference_at = datetime(2026, 9, 5, tzinfo=timezone.utc)
    first = uuid4()
    second = uuid4()
    queue = (
        CRMWorkQueueItem(second, "B", CRMWorkItemType.FOLLOW_UP, reference_at),
        CRMWorkQueueItem(first, "A", CRMWorkItemType.CALL, reference_at + timedelta(days=1)),
    )
    result = CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), work_queue=queue, reference_at=reference_at)
    assert result.work_queue[0].item_type is CRMWorkItemType.CALL
    assert result.work_queue[1].item_type is CRMWorkItemType.FOLLOW_UP


def test_request_user_mismatch_is_rejected():
    tenant_id = uuid4()
    context = RequestContext(tenant=TenantContext(str(tenant_id)), user=UserContext(str(uuid4())))
    with pytest.raises(PermissionError, match="user"):
        CustomerDashboardCompositionService.build(tenant_id=tenant_id, user_id=uuid4(), kpis=_kpis(tenant_id), reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc), request_context=context)
