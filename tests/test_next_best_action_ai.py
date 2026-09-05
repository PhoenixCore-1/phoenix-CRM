from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import (
    AIAvailability,
    AIProposal,
    CRMIntelligenceType,
    CRMAIResult,
    NextBestActionAIService,
    NextBestActionContext,
)


def request_context(tenant_id: UUID, user_id: UUID, customer_id: UUID) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_context_is_immutable_and_copies_values() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    values = {"open_follow_ups": 2, "potential_count": 1}

    context = NextBestActionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values=values,
    )

    values["open_follow_ups"] = 99
    assert context.values["open_follow_ups"] == 2
    with pytest.raises(FrozenInstanceError):
        context.customer_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_core_tenant_and_customer_scope() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = request_context(tenant_id, uuid4(), customer_id)

    built = NextBestActionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"open_follow_ups": 1},
        request_context=context,
    )
    assert built.customer_id == customer_id

    with pytest.raises(PermissionError):
        NextBestActionAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            values={},
            request_context=context,
        )

    with pytest.raises(PermissionError):
        NextBestActionAIService.build_context(
            tenant_id=uuid4(),
            customer_id=customer_id,
            values={},
            request_context=context,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = NextBestActionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        values={},
    )

    result = NextBestActionAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_next_best_action_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = NextBestActionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"open_follow_ups": 2, "overdue_follow_ups": 1},
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
                    customer_id=customer_id,
                    summary="Address the overdue follow-up first.",
                    rationale="The CRM context contains an overdue follow-up.",
                    confidence=0.91,
                    proposed_action="Contact the customer about the overdue follow-up.",
                ),
            )

    capability = FakeCoreAI()
    result = NextBestActionAIService.evaluate(
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
    assert capability.request.context.intelligence_type is CRMIntelligenceType.NEXT_BEST_ACTION
    assert capability.request.context.values["overdue_follow_ups"] == 1


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = NextBestActionContext(tenant_id=tenant_id, customer_id=customer_id, values={})
    request = request_context(tenant_id, user_id, customer_id)

    with pytest.raises(ValueError):
        NextBestActionAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        NextBestActionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        NextBestActionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=NextBestActionContext(tenant_id=tenant_id, customer_id=uuid4(), values={}),
            request_context=request,
        )


def test_wrong_intelligence_type_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = NextBestActionAIService.build_context(
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
        NextBestActionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCapability(),
        )


def test_next_best_action_is_proposal_only_and_non_executing() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = NextBestActionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"open_follow_ups": 1},
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.NEXT_BEST_ACTION,
                    customer_id=customer_id,
                    summary="Follow up with the customer.",
                    rationale="An open follow-up requires attention.",
                    proposed_action="Contact the customer.",
                ),
            )

    result = NextBestActionAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert result.proposal.proposed_action == "Contact the customer."
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "execute_action")
