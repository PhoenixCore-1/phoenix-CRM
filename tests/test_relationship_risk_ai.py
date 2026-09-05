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
    RelationshipRiskAIService,
    RelationshipRiskContext,
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
    values = {"recent_activity_count": 1, "overdue_follow_ups": 2}

    context = RelationshipRiskAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values=values,
    )

    values["overdue_follow_ups"] = 99
    assert context.values["overdue_follow_ups"] == 2
    with pytest.raises(FrozenInstanceError):
        context.customer_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_core_tenant_and_customer_scope() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = request_context(tenant_id, uuid4(), customer_id)

    built = RelationshipRiskAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"overdue_follow_ups": 1},
        request_context=context,
    )
    assert built.customer_id == customer_id

    with pytest.raises(PermissionError):
        RelationshipRiskAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            values={},
            request_context=context,
        )

    with pytest.raises(PermissionError):
        RelationshipRiskAIService.build_context(
            tenant_id=uuid4(),
            customer_id=customer_id,
            values={},
            request_context=context,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = RelationshipRiskAIService.build_context(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        values={},
    )

    result = RelationshipRiskAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_relationship_risk_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = RelationshipRiskAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"recent_activity_count": 0, "overdue_follow_ups": 2},
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.RELATIONSHIP_RISK,
                    customer_id=customer_id,
                    summary="Relationship attention may be required.",
                    rationale="There are overdue follow-ups and no recent activity.",
                    confidence=0.9,
                    proposed_action="Review the relationship and contact the customer.",
                ),
            )

    capability = FakeCoreAI()
    result = RelationshipRiskAIService.evaluate(
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
    assert capability.request.context.intelligence_type is CRMIntelligenceType.RELATIONSHIP_RISK
    assert capability.request.context.values["overdue_follow_ups"] == 2


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = RelationshipRiskContext(tenant_id=tenant_id, customer_id=customer_id, values={})
    request = request_context(tenant_id, user_id, customer_id)

    with pytest.raises(ValueError):
        RelationshipRiskAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        RelationshipRiskAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        RelationshipRiskAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=RelationshipRiskContext(tenant_id=tenant_id, customer_id=uuid4(), values={}),
            request_context=request,
        )


def test_wrong_intelligence_type_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = RelationshipRiskAIService.build_context(
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
        RelationshipRiskAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCapability(),
        )


def test_relationship_risk_is_detection_only_and_non_executing() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = RelationshipRiskAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        values={"recent_activity_count": 0, "overdue_follow_ups": 1},
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.RELATIONSHIP_RISK,
                    customer_id=customer_id,
                    summary="Relationship risk detected.",
                    rationale="Recent engagement has declined.",
                    proposed_action="Review the customer relationship.",
                ),
            )

    result = RelationshipRiskAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert result.proposal.proposed_action is not None
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "execute_action")


def test_unavailable_helper_returns_empty_result() -> None:
    result = RelationshipRiskAIService.unavailable()
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None
