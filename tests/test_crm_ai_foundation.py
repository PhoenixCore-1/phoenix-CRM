"""Tests for Phase 11.1 CRM AI foundation and Core boundary."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import CRMIntelligenceType
from phoenix_crm.services.crm_ai_foundation import (
    AIAvailability,
    CRMAIContext,
    CRMAIResult,
    CRMAIService,
)


def test_build_context_is_tenant_and_customer_scoped():
    tenant_id = uuid4()
    customer_id = uuid4()
    context = CRMAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
        values={"name": "Acme"},
    )
    assert context.tenant_id == tenant_id
    assert context.customer_id == customer_id
    assert context.values["name"] == "Acme"


def test_build_context_rejects_wrong_core_tenant():
    tenant_id = uuid4()
    request = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
    )
    with pytest.raises(PermissionError, match="tenant"):
        CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
            values={},
            request_context=request,
        )


def test_build_context_rejects_customer_outside_core_scope():
    tenant_id = uuid4()
    request = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset()),
    )
    with pytest.raises(PermissionError, match="access scope"):
        CRMAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
            values={},
            request_context=request,
        )


def test_evaluate_gracefully_degrades_without_core_capability():
    tenant_id = uuid4()
    customer_id = uuid4()
    context = CRMAIContext(
        tenant_id=tenant_id,
        customer_id=customer_id,
        intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
        values={},
    )
    result = CRMAIService.evaluate(tenant_id=tenant_id, user_id=uuid4(), context=context)
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_evaluate_rejects_context_tenant_mismatch():
    context = CRMAIContext(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
        values={},
    )
    with pytest.raises(ValueError, match="tenant"):
        CRMAIService.evaluate(tenant_id=uuid4(), user_id=uuid4(), context=context)


def test_evaluate_rejects_request_user_mismatch():
    tenant_id = uuid4()
    context = CRMAIContext(tenant_id, uuid4(), CRMIntelligenceType.CUSTOMER_SUMMARY, {})
    request = RequestContext(TenantContext(str(tenant_id)), UserContext(str(uuid4())))
    with pytest.raises(PermissionError, match="user"):
        CRMAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )


def test_result_contract_enforces_availability_consistency():
    with pytest.raises(ValueError, match="proposal"):
        CRMAIResult(AIAvailability.AVAILABLE)

    with pytest.raises(ValueError, match="proposal"):
        CRMAIResult(AIAvailability.UNAVAILABLE, object())
