"""Tests for Phase 10.4 CRM call and follow-up work queue."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import (
    CallCadence,
    Customer,
    CustomerCallClass,
    CustomerFollowUp,
    FollowUpStatus,
)
from phoenix_crm.services import CustomerCallFollowUpQueueService, CRMWorkItemType


def _customer(tenant_id, *, call_class_id=None, owner_id=None):
    return Customer(
        tenant_id=tenant_id,
        name="Acme",
        customer_type_id=uuid4(),
        call_class_id=call_class_id or uuid4(),
        account_owner_id=owner_id,
    )


def test_builds_call_and_follow_up_items_in_deterministic_order():
    tenant_id = uuid4()
    reference_at = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)
    owner_id = uuid4()
    call_class = CustomerCallClass(uuid4(), "A", "A", CallCadence(7))
    customer = _customer(tenant_id, call_class_id=call_class.id, owner_id=owner_id)
    follow_up = CustomerFollowUp(
        tenant_id=tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=owner_id,
        due_at=reference_at + timedelta(days=1),
        reason="Follow up",
    )

    items = CustomerCallFollowUpQueueService.build(
        tenant_id=tenant_id,
        customers=(customer,),
        follow_ups=(follow_up,),
        call_classes=(call_class,),
        reference_at=reference_at,
    )

    assert len(items) == 2
    assert items[0].item_type is CRMWorkItemType.CALL
    assert items[0].assigned_to_user_id == owner_id
    assert items[1].item_type is CRMWorkItemType.FOLLOW_UP
    assert items[1].follow_up_id == follow_up.id


def test_completed_cancelled_and_rescheduled_follow_ups_are_excluded():
    tenant_id = uuid4()
    customer = _customer(tenant_id)
    due_at = datetime(2026, 9, 5, tzinfo=timezone.utc)
    follow_ups = tuple(
        CustomerFollowUp(
            tenant_id=tenant_id,
            customer_id=customer.id,
            assigned_to_user_id=uuid4(),
            due_at=due_at,
            reason=str(status),
            status=status,
        )
        for status in (FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED, FollowUpStatus.RESCHEDULED)
    )

    items = CustomerCallFollowUpQueueService.build(
        tenant_id=tenant_id,
        customers=(customer,),
        follow_ups=follow_ups,
        reference_at=due_at,
    )

    assert items == ()


def test_tenant_and_customer_scope_are_enforced():
    tenant_id = uuid4()
    other_tenant = uuid4()
    allowed = _customer(tenant_id)
    denied = _customer(tenant_id)
    other = _customer(other_tenant)
    context = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(allowed.id)})),
    )

    items = CustomerCallFollowUpQueueService.build(
        tenant_id=tenant_id,
        customers=(allowed, denied, other),
        request_context=context,
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )

    assert all(item.customer_id == allowed.id for item in items)


def test_wrong_tenant_context_is_rejected():
    tenant_id = uuid4()
    context = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
    )

    with pytest.raises(PermissionError, match="tenant"):
        CustomerCallFollowUpQueueService.build(
            tenant_id=tenant_id,
            request_context=context,
            reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        )


def test_user_filter_and_due_filters_preserve_queue_order():
    tenant_id = uuid4()
    reference_at = datetime(2026, 9, 5, tzinfo=timezone.utc)
    user_id = uuid4()
    customer = _customer(tenant_id, owner_id=user_id)
    follow_up = CustomerFollowUp(
        tenant_id=tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=user_id,
        due_at=reference_at - timedelta(hours=1),
        reason="Urgent follow-up",
        status=FollowUpStatus.DUE,
    )

    items = CustomerCallFollowUpQueueService.build(
        tenant_id=tenant_id,
        customers=(customer,),
        follow_ups=(follow_up,),
        reference_at=reference_at,
    )

    assert CustomerCallFollowUpQueueService.for_user(items, user_id) == items
    assert CustomerCallFollowUpQueueService.due_or_overdue(items, reference_at=reference_at) == items
    assert CustomerCallFollowUpQueueService.overdue(items, reference_at=reference_at) == items


def test_empty_queue_is_valid():
    items = CustomerCallFollowUpQueueService.build(
        tenant_id=uuid4(),
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )
    assert items == ()
