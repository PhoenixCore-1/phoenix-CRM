"""Tests for Phase 11.2 Customer Summary AI."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ActivityType, Customer, CustomerActivity, CustomerFollowUp
from phoenix_crm.services import (
    AIAvailability,
    AIProposal,
    CRMIntelligenceType,
    CRMAIResult,
    CustomerSummaryAIService,
)


def _customer():
    return Customer(uuid4(), "Acme", uuid4(), uuid4())


def _context(customer, *, allowed=True):
    user_id = uuid4()
    scope = AccessScopeContext(
        resource_ids=frozenset({str(customer.id)}) if allowed else frozenset()
    )
    return RequestContext(
        tenant=TenantContext(str(customer.tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=scope,
    ), user_id


def test_build_context_uses_customer_summary_intelligence():
    customer = _customer()
    activity = CustomerActivity(
        customer.tenant_id,
        customer.id,
        ActivityType.CALL,
        "Review",
        datetime.now(timezone.utc),
    )
    follow_up = CustomerFollowUp(
        customer.tenant_id,
        customer.id,
        uuid4(),
        datetime.now(timezone.utc),
        "Follow up",
    )
    context = CustomerSummaryAIService.build_context(customer, [activity], [follow_up])
    assert context.tenant_id == customer.tenant_id
    assert context.customer_id == customer.id
    assert context.intelligence_type is CRMIntelligenceType.CUSTOMER_SUMMARY
    assert context.values["activity_count"] == 1
    assert context.values["follow_up_count"] == 1


def test_build_context_enforces_core_tenant():
    customer = _customer()
    request_context = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
    )
    with pytest.raises(PermissionError, match="tenant"):
        CustomerSummaryAIService.build_context(
            customer, [], [], request_context=request_context
        )


def test_build_context_enforces_customer_access_scope():
    customer = _customer()
    request_context, _ = _context(customer, allowed=False)
    with pytest.raises(PermissionError, match="scope"):
        CustomerSummaryAIService.build_context(
            customer, [], [], request_context=request_context
        )


def test_unavailable_summary_is_graceful():
    result = CustomerSummaryAIService.unavailable()
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


class _StubCoreAI:
    def __init__(self, result):
        self.result = result
        self.request = None

    def evaluate(self, request):
        self.request = request
        return self.result


def test_summary_delegates_to_core_without_provider_knowledge():
    customer = _customer()
    request_context, user_id = _context(customer)
    context = CustomerSummaryAIService.build_context(
        customer, [], [], request_context=request_context
    )
    proposal = AIProposal(
        CRMIntelligenceType.CUSTOMER_SUMMARY,
        customer.id,
        "Healthy relationship with regular engagement.",
        "Recent CRM activity and open follow-up indicate ongoing engagement.",
        confidence=0.9,
    )
    capability = _StubCoreAI(CRMAIResult(AIAvailability.AVAILABLE, proposal))

    result = CustomerSummaryAIService.evaluate(
        tenant_id=customer.tenant_id,
        user_id=user_id,
        context=context,
        capability=capability,
        request_context=request_context,
    )

    assert result is capability.result
    assert capability.request.context is context
    assert capability.request.tenant_id == customer.tenant_id
    assert capability.request.user_id == user_id


def test_summary_rejects_non_summary_context():
    customer = _customer()
    request_context, user_id = _context(customer)
    from phoenix_crm.services import CRMAIService

    context = CRMAIService.build_context(
        tenant_id=customer.tenant_id,
        customer_id=customer.id,
        intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
        values={},
        request_context=request_context,
    )
    with pytest.raises(ValueError, match="customer_summary"):
        CustomerSummaryAIService.evaluate(
            tenant_id=customer.tenant_id,
            user_id=user_id,
            context=context,
            request_context=request_context,
        )
