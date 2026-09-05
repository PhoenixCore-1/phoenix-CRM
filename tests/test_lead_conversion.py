"""Tests for lead-to-customer conversion service."""

from uuid import uuid4

import pytest

from phoenix_crm.domain import Customer, CustomerStatus, Lead, LeadSource, LeadStatus
from phoenix_crm.services import LeadConversionService


def make_lead(**kwargs):
    return Lead(
        tenant_id=kwargs.pop("tenant_id", uuid4()),
        name=kwargs.pop("name", "Acme Lead"),
        source=LeadSource.MANUAL_ENTRY,
        company_name=kwargs.pop("company_name", "Acme Trading"),
        assigned_to_user_id=kwargs.pop("assigned_to_user_id", uuid4()),
        access_scope_id=kwargs.pop("access_scope_id", uuid4()),
        **kwargs,
    )


def make_customer(tenant_id, name):
    return Customer(
        tenant_id=tenant_id,
        name=name,
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )


def potential_lead():
    lead = make_lead()
    lead.start_qualification()
    lead.qualify()
    lead.mark_potential_customer()
    return lead


def test_evaluate_returns_existing_matches_without_mutating_lead():
    lead = potential_lead()
    customer = make_customer(lead.tenant_id, "Acme Trading")
    before = lead.status
    result = LeadConversionService.evaluate(lead, [customer])
    assert result.converted is False
    assert result.customer_id is None
    assert result.existing_customer_matches[0].entity_id == customer.id
    assert lead.status is before


def test_conversion_requires_potential_customer_status():
    lead = make_lead()
    with pytest.raises(ValueError, match="potential customer"):
        LeadConversionService.convert(
            lead, [], customer_type_id=uuid4(), call_class_id=uuid4()
        )


def test_conversion_blocks_existing_customer_match_by_default():
    lead = potential_lead()
    customer = make_customer(lead.tenant_id, "Acme Trading")
    with pytest.raises(ValueError, match="Potential duplicate"):
        LeadConversionService.convert(
            lead, [customer], customer_type_id=uuid4(), call_class_id=uuid4()
        )
    assert lead.status is LeadStatus.POTENTIAL_CUSTOMER


def test_conversion_can_proceed_with_explicit_duplicate_review_override():
    lead = potential_lead()
    existing = make_customer(lead.tenant_id, "Acme Trading")
    customer, result = LeadConversionService.convert(
        lead,
        [existing],
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        duplicate_override_approved=True,
    )
    assert result.converted is True
    assert result.customer_id == customer.id
    assert result.existing_customer_matches[0].entity_id == existing.id
    assert lead.status is LeadStatus.CONVERTED


def test_new_customer_preserves_lead_tenant_and_scope():
    tenant_id = uuid4()
    scope_id = uuid4()
    owner_id = uuid4()
    lead = make_lead(tenant_id=tenant_id, access_scope_id=scope_id, assigned_to_user_id=owner_id)
    lead.start_qualification()
    lead.qualify()
    lead.mark_potential_customer()
    customer, _ = LeadConversionService.convert(
        lead,
        [],
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )
    assert customer.tenant_id == tenant_id
    assert customer.access_scope_id == scope_id
    assert customer.account_owner_id == owner_id


def test_company_name_is_used_for_converted_customer_name():
    lead = make_lead(name="John Smith", company_name="Acme Engineering")
    lead.start_qualification()
    lead.qualify()
    lead.mark_potential_customer()
    customer, _ = LeadConversionService.convert(
        lead, [], customer_type_id=uuid4(), call_class_id=uuid4()
    )
    assert customer.name == "Acme Engineering"


def test_lead_name_is_used_when_company_name_missing():
    lead = make_lead(name="John Smith", company_name=None)
    lead.start_qualification()
    lead.qualify()
    lead.mark_potential_customer()
    customer, _ = LeadConversionService.convert(
        lead, [], customer_type_id=uuid4(), call_class_id=uuid4()
    )
    assert customer.name == "John Smith"


def test_evaluate_is_tenant_safe():
    lead = potential_lead()
    foreign = make_customer(uuid4(), "Acme Trading")
    result = LeadConversionService.evaluate(lead, [foreign])
    assert result.existing_customer_matches == ()


def test_converted_lead_cannot_be_converted_again():
    lead = potential_lead()
    LeadConversionService.convert(
        lead, [], customer_type_id=uuid4(), call_class_id=uuid4()
    )
    assert lead.status is LeadStatus.CONVERTED
    with pytest.raises(ValueError, match="potential customer"):
        LeadConversionService.convert(
            lead, [], customer_type_id=uuid4(), call_class_id=uuid4()
        )


def test_duplicate_block_does_not_change_lead():
    lead = potential_lead()
    before_updated_at = lead.updated_at
    customer = make_customer(lead.tenant_id, "Acme Trading")
    with pytest.raises(ValueError, match="Potential duplicate"):
        LeadConversionService.convert(
            lead, [customer], customer_type_id=uuid4(), call_class_id=uuid4()
        )
    assert lead.status is LeadStatus.POTENTIAL_CUSTOMER
    assert lead.updated_at == before_updated_at
