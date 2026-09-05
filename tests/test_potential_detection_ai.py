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
    PotentialDetectionAIService,
    PotentialDetectionContext,
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
    values = {"current_solutions": ["anchors"], "signals": ["repeat_purchase"]}

    context = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values=values,
    )

    values["signals"] = ["changed"]
    assert context.values["signals"] == ["repeat_purchase"]
    with pytest.raises(FrozenInstanceError):
        context.customer_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_core_tenant_and_customer_scope() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    request = request_context(tenant_id, uuid4(), customer_id)

    built = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"current_solutions": ["anchors"]},
        request_context=request,
    )
    assert built.customer_id == customer_id

    with pytest.raises(PermissionError):
        PotentialDetectionAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            values={},
            request_context=request,
        )

    with pytest.raises(PermissionError):
        PotentialDetectionAIService.build_context(
            tenant_id=uuid4(),
            customer_id=customer_id,
            values={},
            request_context=request,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        values={},
    )

    result = PotentialDetectionAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_potential_detection_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"current_solutions": ["anchors"], "purchase_signals": ["repeat"]},
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.POTENTIAL_DETECTION,
                    customer_id=customer_id,
                    summary="A complementary solution may be relevant.",
                    rationale="The customer has signals consistent with an adjacent need.",
                    confidence=0.86,
                    proposed_action="Discuss the potential solution with the customer.",
                ),
            )

    capability = FakeCoreAI()
    result = PotentialDetectionAIService.evaluate(
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
    assert capability.request.context.intelligence_type is CRMIntelligenceType.POTENTIAL_DETECTION
    assert capability.request.context.values["purchase_signals"] == ["repeat"]


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = PotentialDetectionContext(tenant_id=tenant_id, customer_id=customer_id, values={})
    request = request_context(tenant_id, user_id, customer_id)

    with pytest.raises(ValueError):
        PotentialDetectionAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        PotentialDetectionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        PotentialDetectionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=PotentialDetectionContext(tenant_id=tenant_id, customer_id=uuid4(), values={}),
            request_context=request,
        )


def test_wrong_intelligence_type_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = PotentialDetectionAIService.build_context(
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
        PotentialDetectionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCapability(),
        )


def test_wrong_customer_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={},
    )

    class WrongCustomerCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.POTENTIAL_DETECTION,
                    customer_id=uuid4(),
                    summary="Potential detected.",
                    rationale="The provider returned a mismatched resource.",
                ),
            )

    with pytest.raises(ValueError, match="wrong customer"):
        PotentialDetectionAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCustomerCapability(),
        )


def test_potential_detection_is_proposal_only_and_non_executing() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = PotentialDetectionAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"signals": ["repeat_purchase"]},
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.POTENTIAL_DETECTION,
                    customer_id=customer_id,
                    summary="Potential solution detected.",
                    rationale="The customer's current solution and activity suggest an adjacent need.",
                    proposed_action="Review and discuss the potential with the customer.",
                ),
            )

    result = PotentialDetectionAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert result.proposal.proposed_action is not None
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "create_potential")
    assert not hasattr(result.proposal, "create_opportunity")


def test_unavailable_helper_returns_empty_result() -> None:
    result = PotentialDetectionAIService.unavailable()
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None
