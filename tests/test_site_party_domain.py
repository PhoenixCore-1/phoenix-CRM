"""Tests for the Phase 3.1 project-site party domain model."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import (
    ProjectSiteParty,
    SitePartyMatchStatus,
    SitePartyRole,
    SitePartySource,
)


def make_party() -> ProjectSiteParty:
    return ProjectSiteParty(
        tenant_id=uuid4(),
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="  ABC Contractors  ",
        role=SitePartyRole.MAIN_CONTRACTOR,
    )


def test_defaults_to_unmatched_project_site_discovery() -> None:
    party = make_party()
    assert party.match_status is SitePartyMatchStatus.UNMATCHED
    assert party.source is SitePartySource.PROJECT_SITE_DISCOVERY


def test_stores_external_project_and_site_references() -> None:
    party = make_party()
    assert party.project_id is not None
    assert party.project_site_id is not None
    assert party.tenant_id is not None


def test_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name cannot be empty"):
        ProjectSiteParty(
            tenant_id=uuid4(),
            project_id=uuid4(),
            project_site_id=uuid4(),
            name="   ",
            role=SitePartyRole.OTHER,
        )


def test_normalizes_name_and_notes() -> None:
    party = ProjectSiteParty(
        tenant_id=uuid4(),
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="  ABC Contractors  ",
        role=SitePartyRole.SUBCONTRACTOR,
        notes="  discovered on site  ",
    )
    assert party.name == "ABC Contractors"
    assert party.notes == "discovered on site"


def test_supports_all_site_party_roles() -> None:
    assert len(list(SitePartyRole)) == 9


def test_customer_id_implies_customer_match() -> None:
    customer_id = uuid4()
    party = ProjectSiteParty(
        tenant_id=uuid4(),
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="ABC Contractors",
        role=SitePartyRole.MAIN_CONTRACTOR,
        customer_id=customer_id,
    )
    assert party.customer_id == customer_id
    assert party.match_status is SitePartyMatchStatus.MATCHED_CUSTOMER


def test_link_customer_updates_match_and_timestamp() -> None:
    party = make_party()
    before = party.updated_at
    customer_id = uuid4()
    party.link_customer(customer_id)
    assert party.customer_id == customer_id
    assert party.match_status is SitePartyMatchStatus.MATCHED_CUSTOMER
    assert party.updated_at >= before


def test_mark_potential_lead_clears_customer() -> None:
    party = make_party()
    party.link_customer(uuid4())
    party.mark_potential_lead()
    assert party.customer_id is None
    assert party.match_status is SitePartyMatchStatus.POTENTIAL_LEAD


def test_clear_match_returns_to_unmatched() -> None:
    party = make_party()
    party.link_customer(uuid4())
    party.clear_match()
    assert party.customer_id is None
    assert party.match_status is SitePartyMatchStatus.UNMATCHED


def test_update_notes_normalizes_blank_values() -> None:
    party = make_party()
    party.update_notes("  important party  ")
    assert party.notes == "important party"
    party.update_notes("   ")
    assert party.notes is None


def test_created_and_updated_timestamps_are_utc() -> None:
    party = make_party()
    assert party.created_at.tzinfo == timezone.utc
    assert party.updated_at.tzinfo == timezone.utc
    assert isinstance(party.created_at, datetime)
