"""Tests for Phase 5.3 follow-up Core access-scope enforcement."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Customer, CustomerFollowUp, FollowUpStatus
from phoenix_crm.services import FollowUpService


def make_customer(*, tenant_id=None) -> Customer:
    return Customer(
        tenant_id=tenant_id or uuid4(),
        name="Scoped Customer",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_follow_up(customer: Customer) -> CustomerFollowUp:
    return CustomerFollowUp(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=uuid4(),
        due_at=datetime(2026, 9, 10, 10, tzinfo=timezone.utc),
        reason="Scope test",
    )


def make_context(customer: Customer, *, resources=(), tenant_id=None) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(str(tenant_id or customer.tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset(str(item) for item in resources)),
    )


def test_can_access_when_core_scope_contains_customer():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer, resources=(customer.id,))
    assert FollowUpService.can_access(follow_up, customer, context) is True


def test_can_access_false_when_core_scope_excludes_customer():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer)
    assert FollowUpService.can_access(follow_up, customer, context) is False


def test_can_access_false_for_wrong_tenant():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer, resources=(customer.id,), tenant_id=uuid4())
    assert FollowUpService.can_access(follow_up, customer, context) is False


def test_require_access_raises_when_customer_is_outside_core_scope():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer)
    with pytest.raises(PermissionError, match="access scope"):
        FollowUpService.require_access(follow_up, customer, context)


def test_record_follow_up_requires_core_scope_when_context_is_supplied():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer)
    with pytest.raises(PermissionError):
        FollowUpService.record_follow_up(follow_up, customer, context=context)


def test_complete_requires_core_scope_before_mutating_follow_up():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer)
    with pytest.raises(PermissionError):
        FollowUpService.complete(follow_up, customer, context=context)
    assert follow_up.status is FollowUpStatus.PLANNED


def test_customer_retrieval_returns_nothing_outside_core_scope():
    customer = make_customer()
    follow_up = make_follow_up(customer)
    context = make_context(customer)
    assert FollowUpService.for_customer(customer.id, [follow_up], context=context) == ()


def test_customer_retrieval_returns_only_current_tenant_when_scoped():
    tenant_id = uuid4()
    customer = make_customer(tenant_id=tenant_id)
    follow_up = make_follow_up(customer)
    context = make_context(customer, resources=(customer.id,))
    assert FollowUpService.for_customer(customer.id, [follow_up], context=context) == (follow_up,)


def test_assigned_user_retrieval_filters_to_core_visible_customers():
    user_id = uuid4()
    visible_customer = make_customer()
    hidden_customer = make_customer(tenant_id=visible_customer.tenant_id)
    visible = CustomerFollowUp(
        tenant_id=visible_customer.tenant_id,
        customer_id=visible_customer.id,
        assigned_to_user_id=user_id,
        due_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        reason="Visible",
    )
    hidden = CustomerFollowUp(
        tenant_id=hidden_customer.tenant_id,
        customer_id=hidden_customer.id,
        assigned_to_user_id=user_id,
        due_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
        reason="Hidden",
    )
    context = make_context(visible_customer, resources=(visible_customer.id,))
    result = FollowUpService.assigned_to_user(user_id, [visible, hidden], context=context)
    assert result == (visible,)
