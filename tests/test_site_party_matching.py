"""Tests for Phase 3.2 project-site party matching."""

from uuid import uuid4

import pytest

from phoenix_crm.domain import Customer, CustomerCallClass, CustomerType, ProjectSiteParty, SitePartyRole
from phoenix_crm.services.site_party_matching import MatchOutcome, SitePartyMatchingService


def make_customer(tenant_id, name):
    return Customer(
        tenant_id=tenant_id,
        name=name,
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
    )


def make_party(tenant_id, name):
    return ProjectSiteParty(
        tenant_id=tenant_id,
        project_id=uuid4(),
        project_site_id=uuid4(),
        name=name,
        role=SitePartyRole.MAIN_CONTRACTOR,
    )


def test_normalizes_case_and_whitespace():
    service = SitePartyMatchingService()
    assert service.normalize_name("  ABC   Contractors ") == "abc contractors"


def test_matches_exact_normalized_name_within_tenant():
    tenant_id = uuid4()
    customer = make_customer(tenant_id, "ABC Contractors")
    result = SitePartyMatchingService().find_candidates(
        make_party(tenant_id, "  abc   contractors "), [customer]
    )
    assert result.outcome is MatchOutcome.MATCHED
    assert result.candidates[0].customer_id == customer.id
    assert result.candidates[0].score == 1.0


def test_ignores_customers_from_other_tenants():
    party_tenant = uuid4()
    other_tenant = uuid4()
    result = SitePartyMatchingService().find_candidates(
        make_party(party_tenant, "ABC Contractors"),
        [make_customer(other_tenant, "ABC Contractors")],
    )
    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.candidates == ()


def test_returns_no_match_when_name_is_unknown():
    tenant_id = uuid4()
    result = SitePartyMatchingService().find_candidates(
        make_party(tenant_id, "Unknown Builder"),
        [make_customer(tenant_id, "Known Builder")],
    )
    assert result.outcome is MatchOutcome.NO_MATCH


def test_returns_ambiguous_when_multiple_same_name_customers_exist():
    tenant_id = uuid4()
    first = make_customer(tenant_id, "ABC Contractors")
    second = make_customer(tenant_id, " abc contractors ")
    result = SitePartyMatchingService().find_candidates(
        make_party(tenant_id, "ABC Contractors"), [first, second]
    )
    assert result.outcome is MatchOutcome.AMBIGUOUS
    assert {candidate.customer_id for candidate in result.candidates} == {first.id, second.id}


def test_matching_does_not_mutate_party():
    tenant_id = uuid4()
    customer = make_customer(tenant_id, "ABC Contractors")
    party = make_party(tenant_id, "ABC Contractors")
    SitePartyMatchingService().find_candidates(party, [customer])
    assert party.customer_id is None


def test_explicit_link_updates_party():
    tenant_id = uuid4()
    customer = make_customer(tenant_id, "ABC Contractors")
    party = make_party(tenant_id, "ABC Contractors")
    SitePartyMatchingService().link_match(party, customer)
    assert party.customer_id == customer.id


def test_explicit_link_rejects_cross_tenant_customer():
    party = make_party(uuid4(), "ABC Contractors")
    customer = make_customer(uuid4(), "ABC Contractors")
    with pytest.raises(ValueError, match="another tenant"):
        SitePartyMatchingService().link_match(party, customer)


def test_customer_matching_is_suggestion_not_automatic_linking():
    tenant_id = uuid4()
    customer = make_customer(tenant_id, "ABC Contractors")
    party = make_party(tenant_id, "ABC Contractors")
    result = SitePartyMatchingService().find_candidates(party, [customer])
    assert result.outcome is MatchOutcome.MATCHED
    assert party.customer_id is None


def test_matching_ignores_unused_customer_configuration():
    tenant_id = uuid4()
    customer = Customer(
        tenant_id=tenant_id,
        name="ABC Contractors",
        customer_type_id=CustomerType(uuid4(), "Builder", "builder").id,
        call_class_id=CustomerCallClass(uuid4(), "A Weekly", "A", __import__("phoenix_crm.domain", fromlist=["CallCadence"]).CallCadence(7)).id,
    )
    result = SitePartyMatchingService().find_candidates(
        make_party(tenant_id, "ABC Contractors"), [customer]
    )
    assert result.outcome is MatchOutcome.MATCHED
