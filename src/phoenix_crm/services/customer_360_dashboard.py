"""CRM dashboard foundation contracts for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from phoenix_crm.api import RequestContext


class DashboardMetricKind(str, Enum):
    """Stable semantic kinds for CRM dashboard metrics."""

    COUNT = "count"
    STATUS = "status"
    DATE = "date"


@dataclass(frozen=True, slots=True)
class CustomerDashboardMetric:
    """Immutable dashboard metric/card contract."""

    key: str
    label: str
    kind: DashboardMetricKind
    value: int | str | None
    available: bool = True

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("key cannot be empty")
        if not self.label.strip():
            raise ValueError("label cannot be empty")


@dataclass(frozen=True, slots=True)
class CustomerDashboardSection:
    """Immutable dashboard section containing ordered metrics."""

    key: str
    label: str
    metrics: tuple[CustomerDashboardMetric, ...] = ()
    available: bool = True

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("key cannot be empty")
        if not self.label.strip():
            raise ValueError("label cannot be empty")


@dataclass(frozen=True, slots=True)
class CustomerDashboardFoundation:
    """Read-only foundation for the CRM dashboard.

    Phase 10.1 intentionally defines structure rather than freezing KPI
    calculations. Later phases may populate sections from existing CRM
    services without changing this contract.
    """

    tenant_id: UUID
    user_id: UUID
    sections: tuple[CustomerDashboardSection, ...] = ()

    @property
    def section_keys(self) -> tuple[str, ...]:
        return tuple(section.key for section in self.sections)


class CustomerDashboardFoundationService:
    """Create and validate the dashboard foundation without business logic."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        user_id: UUID,
        sections: tuple[CustomerDashboardSection, ...] = (),
        request_context: RequestContext | None = None,
    ) -> CustomerDashboardFoundation:
        CustomerDashboardFoundationService._require_access(
            tenant_id=tenant_id,
            request_context=request_context,
        )
        ordered = tuple(sections)
        seen: set[str] = set()
        for section in ordered:
            if section.key in seen:
                raise ValueError(f"duplicate dashboard section key: {section.key}")
            seen.add(section.key)
            metric_keys: set[str] = set()
            for metric in section.metrics:
                if metric.key in metric_keys:
                    raise ValueError(
                        f"duplicate dashboard metric key in {section.key}: {metric.key}"
                    )
                metric_keys.add(metric.key)
        return CustomerDashboardFoundation(
            tenant_id=tenant_id,
            user_id=user_id,
            sections=ordered,
        )

    @staticmethod
    def _require_access(*, tenant_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this tenant")
