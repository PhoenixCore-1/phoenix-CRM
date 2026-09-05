"""Platform-facing contracts for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Identifies the tenant within which a CRM operation is executed."""

    tenant_id: str

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")


@dataclass(frozen=True, slots=True)
class UserContext:
    """Identifies the authenticated platform user."""

    user_id: str

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id is required")


@dataclass(frozen=True, slots=True)
class AccessScopeContext:
    """Core-resolved visibility scope consumed by CRM.

    CRM does not calculate organizational access. Core resolves the scope;
    CRM only asks whether a resource is within that resolved scope.
    """

    organization_ids: frozenset[str] = field(default_factory=frozenset)
    unit_ids: frozenset[str] = field(default_factory=frozenset)
    resource_ids: frozenset[str] = field(default_factory=frozenset)
    include_children: bool = True

    def can_access_resource(self, resource_id: str) -> bool:
        return resource_id in self.resource_ids


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Tenant, user and Core-resolved access context for one request."""

    tenant: TenantContext
    user: UserContext
    access_scope: AccessScopeContext = field(default_factory=AccessScopeContext)
    correlation_id: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def can_access_resource(self, resource_id: str) -> bool:
        return self.access_scope.can_access_resource(resource_id)
