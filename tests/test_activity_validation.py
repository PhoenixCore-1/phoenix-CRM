"""Tests for Phase 4.6 activity integrity validation."""

from datetime import datetime, timezone
from uuid import uuid4

from phoenix_crm.domain import (
    ActivityType,
    Contact,
    Customer,
    CustomerActivity,
    CustomerSite,
    ProjectSiteParty,
    SitePartyRole,
    SitePartySource,
)
from phoenix_crm.services import ActivityIntegrityService


def make_customer(*, tenant_id=None) -> Customer:
    return Customer(
        tenant_id=tenant_id or uuid4(),
        name="Acme Customer",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_activity(customer: Customer, **kwargs) -> CustomerActivity:
    return CustomerActivity(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Relationship review",
        occurred_at=datetime.now(timezone.utc),
        **kwargs,
    )


def test_valid_customer_activity_passes():
    customer = make_customer()
    result = ActivityIntegrityService.validate(make_activity(customer), customer)
    assert result.valid is True
    assert result.errors == ()


def test_cross_tenant_activity_fails():
    customer = make_customer()
    activity = CustomerActivity(
        tenant_id=uuid4(),
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Invalid activity",
        occurred_at=datetime.now(timezone.utc),
    )
    result = ActivityIntegrityService.validate(activity, customer)
    assert result.valid is False
    assert "same tenant" in result.errors[0]


def test_contact_must_belong_to_customer():
    customer = make_customer()
    contact = Contact(
        tenant_id=customer.tenant_id,
        customer_id=uuid4(),
        first_name="Jane",
        last_name="Smith",
    )
    activity = make_activity(customer, contact_id=contact.id)
    result = ActivityIntegrityService.validate(activity, customer, contact=contact)
    assert result.valid is False
    assert any("contact must belong" in error for error in result.errors)


def test_site_must_belong_to_customer():
    customer = make_customer()
    site = CustomerSite(
        tenant_id=customer.tenant_id,
        customer_id=uuid4(),
        name="Wrong Customer Site",
    )
    activity = make_activity(customer, site_id=site.id)
    result = ActivityIntegrityService.validate(activity, customer, site=site)
    assert result.valid is False
    assert any("site must belong" in error for error in result.errors)


def test_site_party_for_known_customer_passes():
    customer = make_customer()
    party = ProjectSiteParty(
        tenant_id=customer.tenant_id,
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="Acme Contractor",
        role=SitePartyRole.MAIN_CONTRACTOR,
        source=SitePartySource.PROJECT_SITE_DISCOVERY,
        customer_id=customer.id,
    )
    activity = make_activity(customer, site_party_id=party.id)
    result = ActivityIntegrityService.validate(activity, customer, site_party=party)
    assert result.valid is True


def test_unmatched_site_party_is_allowed():
    customer = make_customer()
    party = ProjectSiteParty(
        tenant_id=customer.tenant_id,
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="Potential Contractor",
        role=SitePartyRole.SUBCONTRACTOR,
        source=SitePartySource.PROJECT_SITE_DISCOVERY,
    )
    activity = make_activity(customer, site_party_id=party.id)
    result = ActivityIntegrityService.validate(activity, customer, site_party=party)
    assert result.valid is True


def test_missing_context_object_is_invalid_when_reference_is_present():
    customer = make_customer()
    activity = make_activity(customer, contact_id=uuid4())
    result = ActivityIntegrityService.validate(activity, customer)
    assert result.valid is False
    assert "matching contact" in result.errors[0]


def test_require_valid_raises_for_invalid_activity():
    customer = make_customer()
    activity = make_activity(customer, site_id=uuid4())
    try:
        ActivityIntegrityService.require_valid(activity, customer)
    except ValueError as exc:
        assert "matching site" in str(exc)
    else:
        raise AssertionError("Expected invalid activity to raise ValueError")
