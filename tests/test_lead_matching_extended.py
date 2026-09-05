"""Additional Phase 6.4 duplicate detection coverage."""

from uuid import uuid4

from phoenix_crm.domain import Customer, CustomerStatus, Lead, LeadSource
from phoenix_crm.services import LeadMatchingService


def lead(tenant, **kwargs):
    return Lead(tenant_id=tenant, name=kwargs.pop("name", "Acme Lead"), source=LeadSource.MANUAL_ENTRY, **kwargs)


def customer(tenant, name):
    return Customer(tenant_id=tenant, name=name, customer_type_id=uuid4(), call_class_id=uuid4(), status=CustomerStatus.ACTIVE)


def test_customer_company_match_is_preferred_to_name_fallback():
    tenant = uuid4()
    item = lead(tenant, name="Jane", company_name="Acme")
    match = customer(tenant, "Acme")
    assert LeadMatchingService.customer_matches(item, [match])[0].matched_fields == ("company_name",)


def test_blank_email_does_not_match():
    tenant = uuid4()
    item = lead(tenant, email="")
    candidate = lead(tenant, email="")
    assert LeadMatchingService.lead_duplicates(item, [candidate]) == []


def test_blank_phone_does_not_match():
    tenant = uuid4()
    item = lead(tenant, phone="")
    candidate = lead(tenant, phone="")
    assert LeadMatchingService.lead_duplicates(item, [candidate]) == []


def test_blank_company_name_does_not_create_company_match():
    tenant = uuid4()
    item = lead(tenant, company_name="")
    candidate = customer(tenant, "Acme")
    assert LeadMatchingService.customer_matches(item, [candidate]) == []


def test_multiple_customer_candidates_are_ordered_by_score_then_id():
    tenant = uuid4()
    item = lead(tenant, name="Acme", company_name="Acme")
    weaker = customer(tenant, "Acme")
    stronger = customer(tenant, "Acme")
    # Customer matching intentionally exposes deterministic candidate identity;
    # duplicate scores are ordered by UUID rather than list insertion order.
    result_one = LeadMatchingService.customer_matches(item, [weaker, stronger])
    result_two = LeadMatchingService.customer_matches(item, [stronger, weaker])
    assert result_one == result_two


def test_lead_match_carries_entity_type():
    tenant = uuid4()
    item = lead(tenant, email="same@example.com")
    candidate = lead(tenant, email="same@example.com")
    assert LeadMatchingService.lead_duplicates(item, [candidate])[0].entity_type == "lead"


def test_customer_match_carries_customer_entity_type():
    tenant = uuid4()
    item = lead(tenant, company_name="Acme")
    candidate = customer(tenant, "Acme")
    assert LeadMatchingService.customer_matches(item, [candidate])[0].entity_type == "customer"


def test_phone_match_handles_punctuation_differences():
    tenant = uuid4()
    item = lead(tenant, phone="(011) 555-1234")
    candidate = lead(tenant, phone="011 555 1234")
    assert LeadMatchingService.lead_duplicates(item, [candidate])[0].score == 90


def test_mobile_match_has_same_strength_as_phone():
    tenant = uuid4()
    item = lead(tenant, mobile="082 555 1234")
    candidate = lead(tenant, mobile="0825551234")
    assert LeadMatchingService.lead_duplicates(item, [candidate])[0].score == 90


def test_customer_matching_remains_same_tenant_even_with_identical_names():
    tenant = uuid4()
    item = lead(tenant, name="Acme")
    candidate = customer(uuid4(), "Acme")
    assert LeadMatchingService.customer_matches(item, [candidate]) == []
