from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import (
    AIAvailability,
    AIProposal,
    CallPreparationAIService,
    CallPreparationContext,
    CRMIntelligenceType,
    CRMAIResult,
)


def make_request_context(tenant_id, user_id, resource_ids):
    return RequestContext(
        tenant=TenantContext(tenant_id=tenant_id),
        user=UserContext(user_id=user_id),
        access_scope=AccessScopeContext(resource_ids=frozenset(resource_ids)),
    )


def test_context_is_immutable_and_copies_values() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    values = {"customer_name": "Acme", "last_interaction": "2026-09-01"}

    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values=values,
    )

    values["customer_name"] = "Changed"
    assert context.tenant_id == tenant_id
    assert context.customer_id == customer_id
    assert context.values["customer_name"] == "Acme"
    with pytest.raises(FrozenInstanceError):
        context.customer_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_core_tenant_and_customer_scope() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    request_context = make_request_context(
        str(tenant_id), str(uuid4()), {str(customer_id)}
    )

    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"customer_name": "Acme"},
        request_context=request_context,
    )
    assert context.customer_id == customer_id

    with pytest.raises(PermissionError):
        CallPreparationAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            values={},
            request_context=request_context,
        )

    with pytest.raises(PermissionError):
        CallPreparationAIService.build_context(
            tenant_id=uuid4(),
            customer_id=customer_id,
            values={},
            request_context=request_context,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        values={"customer_name": "Acme"},
    )

    result = CallPreparationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_call_preparation_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"customer_name": "Acme", "open_follow_ups": 2},
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.CALL_PREPARATION,
                    customer_id=customer_id,
                    summary="Prepare for two open follow-ups.",
                    rationale="The CRM context contains two open follow-ups.",
                    confidence=0.9,
                    proposed_action="Review the follow-ups before calling.",
                ),
            )

    capability = FakeCoreAI()
    result = CallPreparationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=user_id,
        context=context,
        capability=capability,
    )

    assert result.availability is AIAvailability.AVAILABLE
    assert result.proposal is not None
    assert capability.request.tenant_id == tenant_id
    assert capability.request.user_id == user_id
    assert capability.request.context.customer_id == customer_id
    assert capability.request.context.intelligence_type is CRMIntelligenceType.CALL_PREPARATION
    assert capability.request.context.values["open_follow_ups"] == 2


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = CallPreparationContext(tenant_id=tenant_id, customer_id=customer_id, values={})
    request_context = make_request_context(
        str(tenant_id), str(user_id), {str(customer_id)}
    )

    with pytest.raises(ValueError):
        CallPreparationAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request_context,
        )

    with pytest.raises(PermissionError):
        CallPreparationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request_context,
        )

    with pytest.raises(PermissionError):
        CallPreparationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=CallPreparationContext(tenant_id=tenant_id, customer_id=uuid4(), values={}),
            request_context=request_context,
        )


def test_wrong_intelligence_type_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={},
    )

    class WrongCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
                    customer_id=customer_id,
                    summary="Wrong capability output.",
                    rationale="It is intentionally the wrong type.",
                ),
            )

    with pytest.raises(ValueError, match="wrong intelligence type"):
        CallPreparationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCapability(),
        )


def test_call_preparation_result_is_proposal_only_and_non_executing() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = CallPreparationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"customer_name": "Acme"},
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.CALL_PREPARATION,
                    customer_id=customer_id,
                    summary="Review the recent relationship history.",
                    rationale="Recent CRM context should be reviewed before the call.",
                    proposed_action="Review history before contacting the customer.",
                ),
            )

    result = CallPreparationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert result.proposal.proposed_action is not None
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "execute_action")
