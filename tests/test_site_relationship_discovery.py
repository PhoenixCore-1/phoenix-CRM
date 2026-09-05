"""Tests for Phase 3.3 site relationship discovery."""

from uuid import UUID, uuid4

import pytest

from phoenix_crm.domain import ProjectSiteParty, SitePartyRole, SitePartySource
from phoenix_crm.services.site_relationship_discovery import (
    ProjectSiteReference,
    SiteRelationshipDiscoveryService,
)


def make_site() -> ProjectSiteReference:
    return ProjectSiteReference(
        tenant_id=uuid4(),
        project_id=uuid4(),
        project_site_id=uuid4(),
    )


def test_discover_party_uses_external_project_site_reference() -> None:
    site = make_site()
    party = SiteRelationshipDiscoveryService().discover_party(
        site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR
    )
    assert party.tenant_id == site.tenant_id
    assert party.project_id == site.project_id
    assert party.project_site_id == site.project_site_id


def test_discover_party_stores_role_source_and_notes() -> None:
    site = make_site()
    party = SiteRelationshipDiscoveryService().discover_party(
        site,
        "ABC Electrical",
        SitePartyRole.ELECTRICAL_CONTRACTOR,
        source=SitePartySource.SALES_ACTIVITY,
        notes="Found during customer visit",
    )
    assert party.role is SitePartyRole.ELECTRICAL_CONTRACTOR
    assert party.source is SitePartySource.SALES_ACTIVITY
    assert party.notes == "Found during customer visit"


def test_discovery_does_not_create_customer_link() -> None:
    party = SiteRelationshipDiscoveryService().discover_party(
        make_site(), "New Contractor", SitePartyRole.SUBCONTRACTOR
    )
    assert party.customer_id is None


def test_same_party_can_have_multiple_roles_on_same_site() -> None:
    site = make_site()
    service = SiteRelationshipDiscoveryService()
    contractor = service.discover_party(site, "ABC Group", SitePartyRole.SUBCONTRACTOR)
    supplier = service.discover_party(site, "ABC Group", SitePartyRole.SUPPLIER)
    assert contractor.id != supplier.id
    assert contractor.role is SitePartyRole.SUBCONTRACTOR
    assert supplier.role is SitePartyRole.SUPPLIER


def test_duplicate_detection_ignores_case_and_whitespace() -> None:
    site = make_site()
    service = SiteRelationshipDiscoveryService()
    existing = service.discover_party(site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    candidate = service.discover_party(site, "  abc   contractors ", SitePartyRole.MAIN_CONTRACTOR)
    assert service.is_duplicate([existing], candidate) is True


def test_duplicate_detection_allows_different_site() -> None:
    site = make_site()
    other_site = ProjectSiteReference(site.tenant_id, site.project_id, uuid4())
    service = SiteRelationshipDiscoveryService()
    existing = service.discover_party(site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    candidate = service.discover_party(other_site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    assert service.is_duplicate([existing], candidate) is False


def test_duplicate_detection_is_tenant_safe() -> None:
    site = make_site()
    other_tenant = ProjectSiteReference(uuid4(), site.project_id, site.project_site_id)
    service = SiteRelationshipDiscoveryService()
    existing = service.discover_party(site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    candidate = service.discover_party(other_tenant, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    assert service.is_duplicate([existing], candidate) is False


def test_duplicate_detection_allows_different_role() -> None:
    site = make_site()
    service = SiteRelationshipDiscoveryService()
    existing = service.discover_party(site, "ABC Contractors", SitePartyRole.MAIN_CONTRACTOR)
    candidate = service.discover_party(site, "ABC Contractors", SitePartyRole.SUBCONTRACTOR)
    assert service.is_duplicate([existing], candidate) is False


def test_validate_site_reference_accepts_complete_reference() -> None:
    site = make_site()
    SiteRelationshipDiscoveryService.validate_site_reference(site)


def test_validate_site_reference_rejects_empty_tenant() -> None:
    site = ProjectSiteReference(UUID(int=0), uuid4(), uuid4())
    with pytest.raises(ValueError, match="tenant ID"):
        SiteRelationshipDiscoveryService.validate_site_reference(site)


def test_validate_site_reference_rejects_empty_project() -> None:
    site = ProjectSiteReference(uuid4(), UUID(int=0), uuid4())
    with pytest.raises(ValueError, match="Project reference"):
        SiteRelationshipDiscoveryService.validate_site_reference(site)


def test_validate_site_reference_rejects_empty_project_site() -> None:
    site = ProjectSiteReference(uuid4(), uuid4(), UUID(int=0))
    with pytest.raises(ValueError, match="Project site reference"):
        SiteRelationshipDiscoveryService.validate_site_reference(site)
