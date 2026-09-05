"""Platform-facing contracts for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Identifies the tenant within which a CRM operation is executed."""

    tenant_id: str

    def __post_init__(self) -> None:
        tenant_id = self.tenant_id.strip()
        if not tenant_id:
            raise ValueError("tenant_id is required")
        object.__setattr__(self, "tenant_id", tenant_id)


@dataclass(frozen=True, slots=True)
class UserContext:
    """Identifies the authenticated platform user."""

    user_id: str

    def __post_init__(self) -> None:
        user_id = self.user_id.strip()
        if not user_id:
            raise ValueError("user_id is required")
        object.__setattr__(self, "user_id", user_id)


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "organization_ids", self._normalize_ids(self.organization_ids, "organization_ids"))
        object.__setattr__(self, "unit_ids", self._normalize_ids(self.unit_ids, "unit_ids"))
        object.__setattr__(self, "resource_ids", self._normalize_ids(self.resource_ids, "resource_ids"))

    @staticmethod
    def _normalize_ids(values: frozenset[str], field_name: str) -> frozenset[str]:
        normalized = frozenset(value.strip() for value in values)
        if "" in normalized:
            raise ValueError(f"{field_name} cannot contain empty IDs")
        return normalized

    def can_access_resource(self, resource_id: str) -> bool:
        return resource_id.strip() in self.resource_ids


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Tenant, user and Core-resolved access context for one request."""

    tenant: TenantContext
    user: UserContext
    access_scope: AccessScopeContext = field(default_factory=AccessScopeContext)
    correlation_id: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        correlation_id = self.correlation_id.strip()
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        metadata = {str(key).strip(): str(value) for key, value in self.metadata.items()}
        if "" in metadata:
            raise ValueError("metadata keys cannot be empty")
        object.__setattr__(self, "correlation_id", correlation_id)
        object.__setattr__(self, "metadata", MappingProxyType(metadata))

    def can_access_resource(self, resource_id: str) -> bool:
        return self.access_scope.can_access_resource(resource_id)
