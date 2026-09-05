"""Phase 12 activity recording boundary regression tests."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Customer, CustomerActivity
from phoenix_crm.services import ActivityService


def request_context(tenant_id, user_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def make_customer(tenant_id):
    return Customer(tenant_id=tenant_id, name="Boundary Customer")


def make_activity(customer, performer=None):
    return CustomerActivity(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        activity_type="CALL",
        subject="Boundary test",
        occurred_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        performed_by_user_id=performer,
    )


def test_record_activity_requires_customer_in_core_scope():
    tenant = uuid4()
    user = uuid4()
    customer = make_customer(tenant)
    activity = make_activity(customer, user)

    with pytest.raises(PermissionError, match="does not include this customer"):
        ActivityService.record_activity(
            activity,
            customer,
            context=request_context(tenant, user, uuid4()),
        )


def test_record_activity_rejects_mismatched_performer():
    tenant = uuid4()
    user = uuid4()
    other_user = uuid4()
    customer = make_customer(tenant)
    activity = make_activity(customer, other_user)

    with pytest.raises(PermissionError, match="performer does not match"):
        ActivityService.record_activity(
            activity,
            customer,
            context=request_context(tenant, user, customer.id),
        )


def test_record_activity_accepts_matching_core_context():
    tenant = uuid4()
    user = uuid4()
    customer = make_customer(tenant)
    activity = make_activity(customer, user)

    assert ActivityService.record_activity(
        activity,
        customer,
        context=request_context(tenant, user, customer.id),
    ) is activity
