"""Audit contracts for Phoenix CRM 360 Phase 12."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class CRMAuditEvent:
    """Immutable audit event emitted by CRM business services."""

    tenant_id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.action.strip():
            raise ValueError("audit action cannot be empty")
        if not self.resource_type.strip():
            raise ValueError("audit resource_type cannot be empty")
        object.__setattr__(self, "action", self.action.strip())
        object.__setattr__(self, "resource_type", self.resource_type.strip())
        object.__setattr__(self, "correlation_id", self.correlation_id.strip())
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class CRMAuditService:
    """Create audit events without owning persistence or transport."""

    @staticmethod
    def record(
        *,
        tenant_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None = None,
        correlation_id: str = "",
        metadata: Mapping[str, str] | None = None,
    ) -> CRMAuditEvent:
        return CRMAuditEvent(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            metadata={} if metadata is None else metadata,
        )
