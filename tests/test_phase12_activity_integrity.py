"""Phase 12 activity/lead relationship integrity hardening tests."""

from datetime import datetime, timezone
from uuid import uuid4

from phoenix_crm.domain import ActivityType, CustomerActivity, Lead, LeadSource
from phoenix_crm.services import ActivityIntegrityService


def make_lead(*, tenant_id=None) -> Lead:
    return Lead(
        tenant_id=tenant_id or uuid4(),
        name="Potential Customer",
        source=LeadSource.MANUAL_ENTRY,
    )


def make_lead_activity(lead: Lead, **kwargs) -> CustomerActivity:
    return CustomerActivity(
        tenant_id=lead.tenant_id,
        customer_id=None,
        activity_type=ActivityType.CALL,
        subject="Lead qualification call",
        occurred_at=datetime.now(timezone.utc),
        lead_id=lead.id,
        **kwargs,
    )


def test_valid_lead_activity_passes():
    lead = make_lead()
    result = ActivityIntegrityService.validate_lead(make_lead_activity(lead), lead)
    assert result.valid is True
    assert result.errors == ()


def test_lead_activity_cross_tenant_fails():
    lead = make_lead()
    activity = make_lead_activity(lead)
    activity.tenant_id = uuid4()
    result = ActivityIntegrityService.validate_lead(activity, lead)
    assert result.valid is False
    assert "same tenant" in result.errors[0]


def test_lead_activity_wrong_lead_fails():
    lead = make_lead()
    other = make_lead(tenant_id=lead.tenant_id)
    result = ActivityIntegrityService.validate_lead(make_lead_activity(lead), other)
    assert result.valid is False
    assert "does not match" in result.errors[0]


def test_lead_activity_cannot_also_reference_customer():
    lead = make_lead()
    activity = make_lead_activity(lead)
    activity.customer_id = uuid4()
    result = ActivityIntegrityService.validate_lead(activity, lead)
    assert result.valid is False
    assert "cannot reference a customer" in result.errors[0]


def test_customer_activity_rejects_lead_reference():
    lead = make_lead()
    from phoenix_crm.domain import Customer

    customer = Customer(lead.tenant_id, "Customer", uuid4(), uuid4())
    activity = CustomerActivity(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Customer call",
        occurred_at=datetime.now(timezone.utc),
        lead_id=lead.id,
    )
    result = ActivityIntegrityService.validate(activity, customer)
    assert result.valid is False
    assert "both a customer and a lead" in result.errors[0]


def test_require_valid_lead_raises_for_invalid_relationship():
    lead = make_lead()
    other = make_lead(tenant_id=lead.tenant_id)
    activity = make_lead_activity(other)
    try:
        ActivityIntegrityService.require_valid_lead(activity, lead)
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("Expected invalid lead activity to raise ValueError")
