"""Tests for Phase 6.3 lead qualification service."""

from uuid import uuid4

import pytest

from phoenix_crm.domain import Lead, LeadSource, LeadStatus
from phoenix_crm.services import LeadQualificationService


def make_lead() -> Lead:
    return Lead(
        tenant_id=uuid4(),
        name="Qualification Lead",
        source=LeadSource.MANUAL_ENTRY,
    )


def test_start_returns_qualification_result():
    lead = make_lead()
    result = LeadQualificationService.start(lead)
    assert result.lead_id == lead.id
    assert result.status is LeadStatus.QUALIFYING
    assert result.qualified is False
    assert result.rationale is None


def test_qualify_returns_qualified_result_and_strips_rationale():
    lead = make_lead()
    lead.start_qualification()
    result = LeadQualificationService.qualify(lead, rationale="  Meets target customer profile  ")
    assert result.status is LeadStatus.QUALIFIED
    assert result.qualified is True
    assert result.rationale == "Meets target customer profile"


def test_mark_potential_customer_returns_qualified_result():
    lead = make_lead()
    lead.start_qualification()
    lead.qualify()
    result = LeadQualificationService.mark_potential_customer(lead)
    assert result.status is LeadStatus.POTENTIAL_CUSTOMER
    assert result.qualified is True


def test_disqualify_returns_unqualified_result():
    lead = make_lead()
    result = LeadQualificationService.disqualify(lead, rationale="  Outside target market  ")
    assert result.status is LeadStatus.DISQUALIFIED
    assert result.qualified is False
    assert result.rationale == "Outside target market"


def test_qualification_service_preserves_domain_transition_rules():
    lead = make_lead()
    with pytest.raises(ValueError):
        LeadQualificationService.qualify(lead)
    with pytest.raises(ValueError):
        LeadQualificationService.mark_potential_customer(lead)


def test_empty_rationale_is_rejected():
    lead = make_lead()
    lead.start_qualification()
    with pytest.raises(ValueError, match="rationale cannot be empty"):
        LeadQualificationService.qualify(lead, rationale="   ")


def test_disqualification_can_happen_from_qualification_stage():
    lead = make_lead()
    LeadQualificationService.start(lead)
    result = LeadQualificationService.disqualify(lead, rationale="No current requirement")
    assert result.status is LeadStatus.DISQUALIFIED
    assert result.qualified is False
