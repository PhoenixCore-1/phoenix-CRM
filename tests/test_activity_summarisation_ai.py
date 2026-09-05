from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import ActivityOutcome, ActivityType, CustomerActivity
from phoenix_crm.services import (
    AIAvailability,
    AIProposal,
    ActivitySummarisationAIService,
    ActivitySummarisationContext,
    CRMIntelligenceType,
    CRMAIResult,
)


def request_context(tenant_id: UUID, user_id: UUID, customer_id: UUID) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def activity(tenant_id: UUID, customer_id: UUID, subject: str, occurred_at: datetime) -> CustomerActivity:
    return CustomerActivity(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activity_type=ActivityType.CALL,
        subject=subject,
        occurred_at=occurred_at,
        outcome=ActivityOutcome.POSITIVE,
        notes=f"Notes for {subject}",
    )


def test_context_is_immutable_and_contains_deterministically_ordered_activity_data() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    now = datetime.now(timezone.utc)
    older = activity(tenant_id, customer_id, "Older call", now - timedelta(days=2))
    newer = activity(tenant_id, customer_id, "Newer call", now)
    other_tenant = activity(uuid4(), customer_id, "Other tenant", now + timedelta(days=1))
    other_customer = activity(tenant_id, uuid4(), "Other customer", now + timedelta(days=2))

    context = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activities=[older, other_tenant, newer, other_customer],
    )

    assert context.values["activity_count"] == 2
    records = context.values["activities"]
    assert records[0]["subject"] == "Newer call"
    assert records[1]["subject"] == "Older call"
    with pytest.raises(FrozenInstanceError):
        context.customer_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_core_tenant_and_customer_scope() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = request_context(tenant_id, uuid4(), customer_id)

    built = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activities=[],
        request_context=context,
    )
    assert built.customer_id == customer_id

    with pytest.raises(PermissionError):
        ActivitySummarisationAIService.build_context(
            tenant_id=tenant_id,
            customer_id=uuid4(),
            activities=[],
            request_context=context,
        )

    with pytest.raises(PermissionError):
        ActivitySummarisationAIService.build_context(
            tenant_id=uuid4(),
            customer_id=customer_id,
            activities=[],
            request_context=context,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        activities=[],
    )

    result = ActivitySummarisationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_activity_summary_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activities=[activity(tenant_id, customer_id, "Customer call", datetime.now(timezone.utc))],
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.ACTIVITY_SUMMARY,
                    customer_id=customer_id,
                    summary="Recent customer activity was positive.",
                    rationale="The available activity records contain a positive call outcome.",
                    confidence=0.88,
                ),
            )

    capability = FakeCoreAI()
    result = ActivitySummarisationAIService.evaluate(
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
    assert capability.request.context.intelligence_type is CRMIntelligenceType.ACTIVITY_SUMMARY
    assert capability.request.context.values["activity_count"] == 1


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    customer_id = uuid4()
    context = ActivitySummarisationContext(tenant_id=tenant_id, customer_id=customer_id, values={})
    request = request_context(tenant_id, user_id, customer_id)

    with pytest.raises(ValueError):
        ActivitySummarisationAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        ActivitySummarisationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        ActivitySummarisationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=ActivitySummarisationContext(tenant_id=tenant_id, customer_id=uuid4(), values={}),
            request_context=request,
        )


def test_wrong_intelligence_type_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activities=[],
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
        ActivitySummarisationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongCapability(),
        )


def test_activity_summarisation_is_non_executing() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()
    context = ActivitySummarisationAIService.build_context(
        tenant_id=tenant_id,
        customer_id=customer_id,
        activities=[],
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.ACTIVITY_SUMMARY,
                    customer_id=customer_id,
                    summary="Activity summary prepared.",
                    rationale="The activity history was provided to Core AI.",
                    proposed_action="Review the summary with the customer record.",
                ),
            )

    result = ActivitySummarisationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "execute_action")


def test_unavailable_helper_returns_empty_result() -> None:
    result = ActivitySummarisationAIService.unavailable()
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None
