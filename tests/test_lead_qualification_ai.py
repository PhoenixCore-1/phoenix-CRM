from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import (
    AIAvailability,
    AIProposal,
    CRMAIResult,
    CRMIntelligenceType,
    LeadQualificationAIContext,
    LeadQualificationAIService,
)


def request_context(tenant_id: UUID, user_id: UUID, lead_id: UUID) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(lead_id)})),
    )


def test_context_is_immutable_and_copies_values() -> None:
    tenant_id = uuid4()
    lead_id = uuid4()
    values = {"source": "referral", "contactability": "email"}

    context = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=lead_id,
        values=values,
    )

    values["contactability"] = "phone"
    assert context.values["contactability"] == "email"
    with pytest.raises(FrozenInstanceError):
        context.lead_id = uuid4()  # type: ignore[misc]


def test_build_context_enforces_tenant_and_lead_access_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    lead_id = uuid4()
    request = request_context(tenant_id, user_id, lead_id)

    built = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=lead_id,
        values={"source": "website"},
        request_context=request,
    )
    assert built.lead_id == lead_id

    with pytest.raises(ValueError):
        LeadQualificationAIService.build_context(
            tenant_id=uuid4(),
            lead_id=lead_id,
            values={},
            request_context=request,
        )

    with pytest.raises(PermissionError):
        LeadQualificationAIService.build_context(
            tenant_id=tenant_id,
            lead_id=uuid4(),
            values={},
            request_context=request,
        )


def test_evaluate_is_gracefully_unavailable_without_core_capability() -> None:
    tenant_id = uuid4()
    context = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=uuid4(),
        values={},
    )

    result = LeadQualificationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
    )

    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None


def test_core_capability_receives_lead_qualification_request() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    lead_id = uuid4()
    context = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=lead_id,
        values={"source": "project_site_discovery", "company_name": "Example Ltd"},
    )

    class FakeCoreAI:
        def __init__(self) -> None:
            self.request = None

        def evaluate(self, request):
            self.request = request
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.LEAD_QUALIFICATION,
                    customer_id=lead_id,
                    summary="Lead appears suitable for qualification review.",
                    rationale="The lead has a known company and a relevant source.",
                    confidence=0.88,
                    proposed_action="Review qualification signals with the lead owner.",
                ),
            )

    capability = FakeCoreAI()
    result = LeadQualificationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=user_id,
        context=context,
        capability=capability,
    )

    assert result.availability is AIAvailability.AVAILABLE
    assert result.proposal is not None
    assert capability.request.tenant_id == tenant_id
    assert capability.request.user_id == user_id
    assert capability.request.context.customer_id == lead_id
    assert capability.request.context.intelligence_type is CRMIntelligenceType.LEAD_QUALIFICATION
    assert capability.request.context.values["company_name"] == "Example Ltd"


def test_evaluate_enforces_tenant_user_and_resource_scope() -> None:
    tenant_id = uuid4()
    user_id = uuid4()
    lead_id = uuid4()
    context = LeadQualificationAIContext(tenant_id=tenant_id, lead_id=lead_id, values={})
    request = request_context(tenant_id, user_id, lead_id)

    with pytest.raises(ValueError):
        LeadQualificationAIService.evaluate(
            tenant_id=uuid4(),
            user_id=user_id,
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        LeadQualificationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            request_context=request,
        )

    with pytest.raises(PermissionError):
        LeadQualificationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=user_id,
            context=LeadQualificationAIContext(tenant_id=tenant_id, lead_id=uuid4(), values={}),
            request_context=request,
        )


def test_wrong_intelligence_type_or_resource_from_core_is_rejected() -> None:
    tenant_id = uuid4()
    lead_id = uuid4()
    context = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=lead_id,
        values={},
    )

    class WrongTypeCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.CUSTOMER_SUMMARY,
                    customer_id=lead_id,
                    summary="Wrong output.",
                    rationale="Intentionally wrong intelligence type.",
                ),
            )

    with pytest.raises(ValueError, match="wrong intelligence type"):
        LeadQualificationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongTypeCapability(),
        )

    wrong_lead = uuid4()

    class WrongResourceCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.LEAD_QUALIFICATION,
                    customer_id=wrong_lead,
                    summary="Wrong resource.",
                    rationale="Intentionally wrong lead identifier.",
                ),
            )

    with pytest.raises(ValueError, match="wrong resource"):
        LeadQualificationAIService.evaluate(
            tenant_id=tenant_id,
            user_id=uuid4(),
            context=context,
            capability=WrongResourceCapability(),
        )


def test_proposal_is_assistance_only_and_does_not_qualify_or_convert() -> None:
    tenant_id = uuid4()
    lead_id = uuid4()
    context = LeadQualificationAIService.build_context(
        tenant_id=tenant_id,
        lead_id=lead_id,
        values={"qualification_signals": ["known company", "valid contact"]},
    )

    class ProposalCapability:
        def evaluate(self, request):
            return CRMAIResult(
                AIAvailability.AVAILABLE,
                AIProposal(
                    intelligence_type=CRMIntelligenceType.LEAD_QUALIFICATION,
                    customer_id=lead_id,
                    summary="Lead should be reviewed for qualification.",
                    rationale="The supplied signals indicate a potentially valid lead.",
                    confidence=0.91,
                    proposed_action="Review and decide whether to qualify the lead.",
                ),
            )

    result = LeadQualificationAIService.evaluate(
        tenant_id=tenant_id,
        user_id=uuid4(),
        context=context,
        capability=ProposalCapability(),
    )

    assert result.proposal is not None
    assert result.proposal.proposed_action is not None
    assert not hasattr(result.proposal, "execute")
    assert not hasattr(result.proposal, "convert")


def test_unavailable_helper_returns_empty_result() -> None:
    result = LeadQualificationAIService.unavailable()
    assert result.availability is AIAvailability.UNAVAILABLE
    assert result.proposal is None
