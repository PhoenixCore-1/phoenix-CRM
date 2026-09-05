"""Tests for Phase 6.8 lead AI assistance."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import Customer, CustomerActivity, CustomerStatus, Lead, LeadSource
from phoenix_crm.services import LeadAIService, LeadIntelligenceType


def make_lead(tenant_id=None):
    return Lead(
        tenant_id=tenant_id or uuid4(),
        name="AI Lead",
        source=LeadSource.MANUAL_ENTRY,
        company_name="AI Trading",
    )


def make_context(lead, *, allowed=True, tenant_id=None):
    return RequestContext(
        tenant=TenantContext(str(tenant_id or lead.tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(
            resource_ids=frozenset({str(lead.id)}) if allowed else frozenset()
        ),
    )


def test_context_for_lead_is_deterministic_and_tenant_scoped():
    lead = make_lead()
    context = LeadAIService.context_for_lead(lead, context=make_context(lead))
    assert context.lead_id == lead.id
    assert context.tenant_id == lead.tenant_id
    assert context.lead_name == "AI Lead"
    assert context.source == LeadSource.MANUAL_ENTRY.value
    assert context.activity_count == 0
    assert context.follow_up_count == 0


def test_context_includes_only_matching_lead_activities():
    lead = make_lead()
    activity = CustomerActivity(
        tenant_id=lead.tenant_id,
        customer_id=uuid4(),
        activity_type="note",
        subject="Lead note",
        occurred_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        metadata={"lead_id": str(lead.id)},
    )
    other = CustomerActivity(
        tenant_id=lead.tenant_id,
        customer_id=uuid4(),
        activity_type="note",
        subject="Other",
        occurred_at=activity.occurred_at,
        metadata={"lead_id": str(uuid4())},
    )
    result = LeadAIService.context_for_lead(
        lead, activities=[activity, other], context=make_context(lead)
    )
    assert result.activity_count == 1


def test_context_includes_customer_duplicate_matches():
    lead = make_lead()
    customer = Customer(
        tenant_id=lead.tenant_id,
        name="AI Trading",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        status=CustomerStatus.ACTIVE,
    )
    result = LeadAIService.context_for_lead(
        lead, customers=[customer], context=make_context(lead)
    )
    assert result.customer_matches[0].entity_id == customer.id
    assert result.customer_matches[0].score == 60


def test_context_blocks_wrong_tenant():
    lead = make_lead()
    with pytest.raises(PermissionError, match="tenant"):
        LeadAIService.context_for_lead(
            lead, context=make_context(lead, tenant_id=uuid4())
        )


def test_context_blocks_out_of_scope_lead():
    lead = make_lead()
    with pytest.raises(PermissionError, match="scope"):
        LeadAIService.context_for_lead(lead, context=make_context(lead, allowed=False))


def test_proposal_is_non_executing_and_preserves_confidence():
    lead = make_lead()
    proposal = LeadAIService.proposal(
        LeadIntelligenceType.QUALIFICATION_ASSISTANCE,
        lead,
        summary="Lead appears suitable for qualification.",
        rationale="Company profile and source indicate a potential fit.",
        confidence=0.84,
        proposed_action="Review and qualify the lead.",
        context=make_context(lead),
    )
    assert proposal.lead_id == lead.id
    assert proposal.confidence == 0.84
    assert lead.status.value == "new"


def test_proposal_rejects_invalid_confidence():
    lead = make_lead()
    with pytest.raises(ValueError, match="between 0 and 1"):
        LeadAIService.proposal(
            LeadIntelligenceType.NEXT_BEST_ACTION,
            lead,
            summary="Action",
            rationale="Reason",
            confidence=1.1,
        )


def test_proposal_requires_non_empty_content():
    lead = make_lead()
    with pytest.raises(ValueError, match="summary"):
        LeadAIService.proposal(
            LeadIntelligenceType.LEAD_SUMMARY,
            lead,
            summary=" ",
            rationale="Reason",
        )
