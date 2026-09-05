"""Tests for the Phase 6.7 Core access-scope boundary."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Lead, LeadSource
from phoenix_crm.services import LeadAccessService, LeadQualificationService


def make_lead(tenant_id=None):
    return Lead(
        tenant_id=tenant_id or uuid4(),
        name="Scoped Lead",
        source=LeadSource.MANUAL_ENTRY,
    )


def make_context(lead, *, tenant_id=None, resource_ids=()):
    return RequestContext(
        tenant=TenantContext(str(tenant_id or lead.tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset(str(item) for item in resource_ids)),
    )


def test_can_access_requires_same_tenant_and_core_resource_scope():
    lead = make_lead()
    allowed = make_context(lead, resource_ids=(lead.id,))
    denied = make_context(lead)
    foreign = make_context(lead, tenant_id=uuid4(), resource_ids=(lead.id,))
    assert LeadAccessService.can_access(lead, allowed) is True
    assert LeadAccessService.can_access(lead, denied) is False
    assert LeadAccessService.can_access(lead, foreign) is False


def test_require_access_raises_when_core_scope_excludes_lead():
    lead = make_lead()
    with pytest.raises(PermissionError, match="does not include this lead"):
        LeadAccessService.require_access(lead, make_context(lead))


def test_filter_accessible_uses_core_scope():
    first = make_lead()
    second = make_lead(tenant_id=first.tenant_id)
    context = make_context(first, resource_ids=(first.id,))
    assert LeadAccessService.filter_accessible([first, second], context) == (first,)


def test_qualification_rejects_lead_outside_core_scope():
    lead = make_lead()
    context = make_context(lead)
    with pytest.raises(PermissionError, match="does not include this lead"):
        LeadQualificationService.start(lead, context=context)
    assert lead.status.value == "new"


def test_qualification_accepts_core_scoped_lead():
    lead = make_lead()
    context = make_context(lead, resource_ids=(lead.id,))
    result = LeadQualificationService.start(lead, context=context)
    assert result.status.value == "qualifying"
