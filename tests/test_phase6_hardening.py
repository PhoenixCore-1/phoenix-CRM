"""Phase 6 hardening regression tests."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Customer, CustomerStatus, Lead, LeadSource, LeadStatus
from phoenix_crm.services import (
    LeadConversionService,
    LeadMatchingService,
    LeadQualificationService,
)


def make_lead(**kwargs):
    return Lead(
        tenant_id=kwargs.pop("tenant_id", uuid4()),
        name=kwargs.pop("name", "Acme Lead"),
        source=LeadSource.MANUAL_ENTRY,
        company_name=kwargs.pop("company_name", "Acme Trading"),
        **kwargs,
    )


def scoped_context(lead, *, allowed=True, tenant_id=None):
    return RequestContext(
        tenant=TenantContext(str(tenant_id or lead.tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(
            resource_ids=frozenset({str(lead.id)}) if allowed else frozenset()
        ),
    )


def potential_lead(**kwargs):
    lead = make_lead(**kwargs)
    LeadQualificationService.start(lead)
    LeadQualificationService.qualify(lead)
    LeadQualificationService.mark_potential_customer(lead)
    return lead


def test_access_scope_denial_does_not_mutate_lead():
    lead = make_lead()
    before = lead.updated_at
    with pytest.raises(PermissionError):
        LeadQualificationService.start(lead, context=scoped_context(lead, allowed=False))
    assert lead.status is LeadStatus.NEW
    assert lead.updated_at == before


def test_conversion_scope_is_checked_before_lifecycle_mutation():
    lead = potential_lead()
    before = lead.updated_at
    with pytest.raises(PermissionError):
        LeadConversionService.convert(
            lead,
            [],
            customer_type_id=uuid4(),
            call_class_id=uuid4(),
            context=scoped_context(lead, allowed=False),
        )
    assert lead.status is LeadStatus.POTENTIAL_CUSTOMER
    assert lead.updated_at == before


def test_customer_matching_never_crosses_tenant_boundary():
    lead = potential_lead()
    foreign = Customer(
        tenant_id=uuid4(),
        name="Acme Trading",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )
    assert LeadMatchingService.customer_matches(lead, [foreign]) == []


def test_lead_matching_requires_identity_signal():
    lead = make_lead(company_name=None)
    candidate = make_lead(tenant_id=lead.tenant_id, company_name=None, name=lead.name)
    assert LeadMatchingService.lead_duplicates(lead, [candidate]) == []


def test_duplicate_block_preserves_lead_when_override_is_not_approved():
    lead = potential_lead()
    customer = Customer(
        tenant_id=lead.tenant_id,
        name=lead.company_name,
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )
    before = lead.updated_at
    with pytest.raises(ValueError, match="Potential duplicate"):
        LeadConversionService.convert(
            lead,
            [customer],
            customer_type_id=uuid4(),
            call_class_id=uuid4(),
        )
    assert lead.status is LeadStatus.POTENTIAL_CUSTOMER
    assert lead.updated_at == before
