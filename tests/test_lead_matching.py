"""Tests for Phase 6.4 lead duplicate and customer matching."""

from uuid import uuid4

from phoenix_crm.domain import Customer, CustomerStatus, Lead, LeadSource
from phoenix_crm.services import LeadMatchingService


def make_lead(tenant_id=None, **kwargs):
    return Lead(tenant_id=tenant_id or uuid4(), name=kwargs.pop("name", "Acme Lead"), source=LeadSource.MANUAL_ENTRY, **kwargs)


def make_customer(tenant_id, name="Acme Customer"):
    return Customer(
        tenant_id=tenant_id,
        name=name,
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )


def test_normalize_is_case_and_whitespace_insensitive():
    assert LeadMatchingService.normalize("  ACME   Trading ") == "acme trading"


def test_exact_email_is_strongest_lead_duplicate_signal():
    tenant = uuid4()
    lead = make_lead(tenant, email="sales@acme.co.za")
    candidate = make_lead(tenant, name="Different Name", email=" SALES@ACME.CO.ZA ")
    result = LeadMatchingService.lead_duplicates(lead, [candidate])
    assert result[0].entity_id == candidate.id
    assert result[0].score == 100
    assert result[0].matched_fields == ("email",)


def test_multiple_matching_fields_accumulate_score():
    tenant = uuid4()
    lead = make_lead(tenant, name="Acme Lead", company_name="Acme Trading", phone="012 345 6789")
    candidate = make_lead(tenant, name=" acme lead ", company_name="ACME TRADING", phone="0123456789")
    result = LeadMatchingService.lead_duplicates(lead, [candidate])
    assert result[0].score == 150
    assert set(result[0].matched_fields) == {"name", "company_name", "phone"}


def test_phone_formatting_is_normalized():
    tenant = uuid4()
    lead = make_lead(tenant, phone="+27 (12) 345-6789")
    candidate = make_lead(tenant, name="Different Name", phone="27123456789")
    assert LeadMatchingService.lead_duplicates(lead, [candidate])[0].matched_fields == ("phone",)


def test_different_tenants_are_never_matched():
    lead = make_lead(uuid4(), email="same@example.com")
    candidate = make_lead(uuid4(), email="same@example.com")
    assert LeadMatchingService.lead_duplicates(lead, [candidate]) == []


def test_same_lead_is_excluded():
    lead = make_lead(email="same@example.com")
    assert LeadMatchingService.lead_duplicates(lead, [lead]) == []


def test_duplicate_results_are_deterministically_ordered_by_score_then_id():
    tenant = uuid4()
    lead = make_lead(tenant, email="same@example.com", name="Acme")
    weak = make_lead(tenant, name="Acme", email="different@example.com", company_name="Acme Trading")
    strong = make_lead(tenant, name="Acme", email="same@example.com")
    result = LeadMatchingService.lead_duplicates(lead, [weak, strong])
    assert [match.entity_id for match in result] == [strong.id, weak.id]


def test_customer_match_uses_company_name_when_present():
    tenant = uuid4()
    lead = make_lead(tenant, name="John Smith", company_name="Acme Trading")
    customer = make_customer(tenant, " ACME TRADING ")
    result = LeadMatchingService.customer_matches(lead, [customer])
    assert result[0].entity_id == customer.id
    assert result[0].matched_fields == ("company_name",)


def test_customer_match_requires_company_identity_signal():
    tenant = uuid4()
    lead = make_lead(tenant, name="Acme Trading")
    customer = make_customer(tenant, "acme trading")
    assert result := LeadMatchingService.customer_matches(lead, [customer])
    assert result[0].matched_fields == ()


def test_customer_matches_do_not_cross_tenants():
    tenant = uuid4()
    lead = make_lead(tenant, company_name="Acme Trading")
    customer = make_customer(uuid4(), "Acme Trading")
    assert LeadMatchingService.customer_matches(lead, [customer]) == []
