"""Tests for Phase 5.7 CRM AI intelligence foundation."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import ActivityType, Customer, CustomerActivity, CustomerFollowUp
from phoenix_crm.services import AIProposal, CRMIntelligenceService, CRMIntelligenceType


def customer():
    return Customer(uuid4(), "Acme", uuid4(), uuid4())


def test_supported_intelligence_types_are_explicit():
    assert {item.value for item in CRMIntelligenceType} == {
        "customer_summary", "call_preparation", "next_best_action",
        "relationship_risk", "activity_summary", "lead_qualification",
        "potential_detection",
    }


def test_context_is_customer_and_tenant_scoped():
    c = customer()
    other = customer()
    activity = CustomerActivity(c.tenant_id, c.id, ActivityType.CALL, "Call", datetime.now(timezone.utc))
    other_activity = CustomerActivity(other.tenant_id, other.id, ActivityType.CALL, "Call", datetime.now(timezone.utc))
    follow_up = CustomerFollowUp(c.tenant_id, c.id, uuid4(), datetime.now(timezone.utc), "Follow up")
    other_follow_up = CustomerFollowUp(other.tenant_id, other.id, uuid4(), datetime.now(timezone.utc), "Follow up")
    context = CRMIntelligenceService.context_for_customer(
        c, [activity, other_activity], [follow_up, other_follow_up]
    )
    assert context["customer_id"] == str(c.id)
    assert context["tenant_id"] == str(c.tenant_id)
    assert context["activity_count"] == 1
    assert context["follow_up_count"] == 1


def test_proposal_wraps_provider_result_without_executing_action():
    c = customer()
    result = CRMIntelligenceService.proposal(
        CRMIntelligenceType.NEXT_BEST_ACTION,
        c,
        summary="Call the customer",
        rationale="Cadence contact is approaching",
        confidence=0.9,
        proposed_action="Schedule a call",
    )
    assert isinstance(result, AIProposal)
    assert result.customer_id == c.id
    assert result.proposed_action == "Schedule a call"


def test_empty_summary_is_rejected():
    with pytest.raises(ValueError, match="summary"):
        CRMIntelligenceService.proposal(
            CRMIntelligenceType.CUSTOMER_SUMMARY, customer(), summary=" ", rationale="reason"
        )


def test_empty_rationale_is_rejected():
    with pytest.raises(ValueError, match="rationale"):
        CRMIntelligenceService.proposal(
            CRMIntelligenceType.CUSTOMER_SUMMARY, customer(), summary="summary", rationale=" "
        )


def test_confidence_is_bounded():
    with pytest.raises(ValueError, match="confidence"):
        CRMIntelligenceService.proposal(
            CRMIntelligenceType.CUSTOMER_SUMMARY, customer(), summary="summary", rationale="reason", confidence=1.1
        )


def test_confidence_can_be_omitted():
    result = CRMIntelligenceService.proposal(
        CRMIntelligenceType.CUSTOMER_SUMMARY, customer(), summary="summary", rationale="reason"
    )
    assert result.confidence is None
