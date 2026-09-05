"""Tests for Phase 3.4 project-site party lifecycle management."""

from uuid import uuid4

from phoenix_crm.domain import ProjectSiteParty, SitePartyMatchStatus, SitePartyRole, SitePartyStatus


def make_party() -> ProjectSiteParty:
    return ProjectSiteParty(
        tenant_id=uuid4(),
        project_id=uuid4(),
        project_site_id=uuid4(),
        name="ABC Contractors",
        role=SitePartyRole.MAIN_CONTRACTOR,
    )


def test_new_site_party_is_active():
    assert make_party().status is SitePartyStatus.ACTIVE


def test_deactivate_preserves_relationship_record():
    party = make_party()
    party_id = party.id
    party.deactivate()
    assert party.id == party_id
    assert party.status is SitePartyStatus.INACTIVE


def test_reactivate_restores_active_status():
    party = make_party()
    party.deactivate()
    party.reactivate()
    assert party.status is SitePartyStatus.ACTIVE


def test_remove_preserves_record_as_removed():
    party = make_party()
    party_id = party.id
    party.remove()
    assert party.id == party_id
    assert party.status is SitePartyStatus.REMOVED


def test_link_customer_reactivates_relationship():
    party = make_party()
    party.deactivate()
    customer_id = uuid4()
    party.link_customer(customer_id)
    assert party.customer_id == customer_id
    assert party.match_status is SitePartyMatchStatus.MATCHED_CUSTOMER
    assert party.status is SitePartyStatus.ACTIVE


def test_mark_potential_lead_reactivates_relationship():
    party = make_party()
    party.remove()
    party.mark_potential_lead()
    assert party.customer_id is None
    assert party.match_status is SitePartyMatchStatus.POTENTIAL_LEAD
    assert party.status is SitePartyStatus.ACTIVE


def test_clear_match_does_not_change_lifecycle_status():
    party = make_party()
    party.link_customer(uuid4())
    party.clear_match()
    assert party.match_status is SitePartyMatchStatus.UNMATCHED
    assert party.status is SitePartyStatus.ACTIVE


def test_lifecycle_changes_update_timestamp():
    party = make_party()
    before = party.updated_at
    party.deactivate()
    assert party.updated_at >= before
    before = party.updated_at
    party.reactivate()
    assert party.updated_at >= before
    before = party.updated_at
    party.remove()
    assert party.updated_at >= before
