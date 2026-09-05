from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ProjectSiteParty, SitePartyRole, SitePartyStatus
from phoenix_crm.services import Customer360ProjectSiteSection, Customer360ProjectsService, Customer360Reference


def context(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_build_projects_and_project_sites_as_read_only_references():
    tenant_id, customer_id = uuid4(), uuid4()
    project = Customer360Reference("projects", "project", uuid4(), "Project Alpha", "active")
    project_site = Customer360Reference("projects", "project_site", uuid4(), "Site Alpha", "active")
    section = Customer360ProjectsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        project_references=(project,),
        project_site_references=(project_site,),
    )
    assert isinstance(section, Customer360ProjectSiteSection)
    assert section.projects == (project,)
    assert section.project_sites == (project_site,)
    assert section.site_parties == ()


def test_build_includes_only_active_crm_site_party_relationships_for_customer():
    tenant_id, customer_id = uuid4(), uuid4()
    active = ProjectSiteParty(tenant_id, uuid4(), uuid4(), "Main Contractor", SitePartyRole.MAIN_CONTRACTOR, customer_id=customer_id)
    inactive = ProjectSiteParty(tenant_id, uuid4(), uuid4(), "Old Contractor", SitePartyRole.SUBCONTRACTOR, customer_id=customer_id)
    inactive.status = SitePartyStatus.INACTIVE
    other_customer = ProjectSiteParty(tenant_id, uuid4(), uuid4(), "Other Customer", SitePartyRole.ENGINEER, customer_id=uuid4())
    section = Customer360ProjectsService.build(
        tenant_id=tenant_id, customer_id=customer_id, site_parties=(active, inactive, other_customer)
    )
    assert len(section.site_parties) == 1
    assert section.site_parties[0].label == "Main Contractor"
    assert section.site_parties[0].resource_type == "project_site_party"


def test_build_enforces_core_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(PermissionError):
        Customer360ProjectsService.build(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=context(tenant_id, uuid4()),
        )


def test_build_gracefully_returns_empty_when_projects_capability_is_unavailable():
    tenant_id, customer_id = uuid4(), uuid4()
    section = Customer360ProjectsService.build(tenant_id=tenant_id, customer_id=customer_id)
    assert section.projects == ()
    assert section.project_sites == ()
    assert section.site_parties == ()


def test_provider_is_optional_and_contract_based():
    tenant_id, customer_id = uuid4(), uuid4()

    class Provider:
        def references_for_customer(self, *, tenant_id, customer_id):
            return (Customer360Reference("projects", "project", uuid4(), "Provider Project"),)

    section = Customer360ProjectsService.build(
        tenant_id=tenant_id, customer_id=customer_id, provider=Provider()
    )
    assert [item.label for item in section.projects] == ["Provider Project"]


def test_project_reference_filtering_is_deterministic_and_does_not_mutate_inputs():
    tenant_id, customer_id = uuid4(), uuid4()
    project_b = Customer360Reference("projects", "project", uuid4(), "Beta")
    ignored = Customer360Reference("projects", "opportunity", uuid4(), "Not A Project")
    project_a = Customer360Reference("projects", "project", uuid4(), "Alpha")
    refs = (project_b, ignored, project_a)
    section = Customer360ProjectsService.build(
        tenant_id=tenant_id, customer_id=customer_id, project_references=refs
    )
    assert [item.label for item in section.projects] == ["Alpha", "Beta"]
    assert refs == (project_b, ignored, project_a)


def test_build_is_read_only_for_site_party_domain_objects():
    tenant_id, customer_id = uuid4(), uuid4()
    party = ProjectSiteParty(tenant_id, uuid4(), uuid4(), "Contractor", SitePartyRole.MAIN_CONTRACTOR, customer_id=customer_id)
    before = (party.customer_id, party.status, party.notes)
    Customer360ProjectsService.build(tenant_id=tenant_id, customer_id=customer_id, site_parties=(party,))
    assert (party.customer_id, party.status, party.notes) == before
