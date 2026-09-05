"""Core-aligned AI foundation contracts for Phoenix CRM 360.

CRM owns AI use cases and proposal presentation. Phoenix Core owns the
provider, tenant isolation, permissions, governance, audit, usage/cost
controls, and authorization boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.ai_intelligence import AIProposal, CRMIntelligenceType


class AIAvailability(str, Enum):
    """Availability of the Core AI capability for the current request."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class CRMAIContext:
    """Tenant-scoped, permission-filtered context passed to Core AI."""

    tenant_id: UUID
    customer_id: UUID
    intelligence_type: CRMIntelligenceType
    values: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CRMAIRequest:
    """Provider-independent request envelope for a CRM AI use case."""

    tenant_id: UUID
    user_id: UUID
    context: CRMAIContext
    request_context: RequestContext | None = None


@dataclass(frozen=True, slots=True)
class CRM AIResult:
    """Result envelope returned by the Core AI capability boundary."""

    availability: AIAvailability
    proposal: AIProposal | None = None

    def __post_init__(self) -> None:
        if self.availability is AIAvailability.AVAILABLE and self.proposal is None:
            raise ValueError("available AI result requires a proposal")
        if self.availability is AIAvailability.UNAVAILABLE and self.proposal is not None:
            raise ValueError("unavailable AI result must not contain a proposal")


class CoreAICapability(Protocol):
    """Published Core capability consumed by CRM without provider knowledge."""

    def evaluate(self, request: CRM AIRequest) -> CRM AIResult:
        """Evaluate a CRM AI request through the Core-governed AI boundary."""
        ...


class CRM AIService:
    """Enforce CRM/Core AI boundaries before invoking an optional provider."""

    @staticmethod
    def build_context(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        intelligence_type: CRMIntelligenceType,
        values: Mapping[str, object],
        request_context: RequestContext | None = None,
    ) -> CRM AIContext:
        """Build immutable AI context and enforce Core tenant scope."""
        if request_context is not None:
            if request_context.tenant.tenant_id != str(tenant_id):
                raise PermissionError("Core AI request tenant does not match CRM tenant")
            if not request_context.can_access_resource(str(customer_id)):
                raise PermissionError("Core AI request is outside customer access scope")
        return CRM AIContext(
            tenant_id=tenant_id,
            customer_id=customer_id,
            intelligence_type=intelligence_type,
            values=dict(values),
        )

    @staticmethod
    def evaluate(
        *,
        tenant_id: UUID,
        user_id: UUID,
        context: CRM AIContext,
        capability: CoreAICapability | None = None,
        request_context: RequestContext | None = None,
    ) -> CRM AIResult:
        """Evaluate through Core when available; otherwise degrade gracefully."""
        if context.tenant_id != tenant_id:
            raise ValueError("CRM AI context does not match tenant")
        if request_context is not None:
            if request_context.tenant.tenant_id != str(tenant_id):
                raise PermissionError("Core AI request tenant does not match CRM tenant")
            if request_context.user.user_id != str(user_id):
                raise PermissionError("Core AI request user does not match CRM user")
            if not request_context.can_access_resource(str(context.customer_id)):
                raise PermissionError("Core AI request is outside customer access scope")
        if capability is None:
            return CRM AIResult(AIAvailability.UNAVAILABLE)
        return capability.evaluate(
            CRM AIRequest(
                tenant_id=tenant_id,
                user_id=user_id,
                context=context,
                request_context=request_context,
            )
        )
