"""CRM dashboard composition for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.customer_360_dashboard import (
    CustomerDashboardFoundation,
    CustomerDashboardFoundationService,
    CustomerDashboardMetric,
    CustomerDashboardSection,
    DashboardMetricKind,
)
from phoenix_crm.services.customer_360_kpis import CustomerDashboardKPIs
from phoenix_crm.services.customer_call_follow_up_queue import CRMWorkQueueItem


@dataclass(frozen=True, slots=True)
class CustomerDashboardComposition:
    """Immutable complete CRM dashboard read model."""

    foundation: CustomerDashboardFoundation
    kpis: CustomerDashboardKPIs
    work_queue: tuple[CRMWorkQueueItem, ...]
    sections: tuple[CustomerDashboardSection, ...]

    @property
    def tenant_id(self) -> UUID:
        return self.foundation.tenant_id

    @property
    def user_id(self) -> UUID:
        return self.foundation.user_id


class CustomerDashboardCompositionService:
    """Compose frozen KPI, work-queue, and dashboard contracts only."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        user_id: UUID,
        kpis: CustomerDashboardKPIs,
        work_queue: tuple[CRMWorkQueueItem, ...] | list[CRMWorkQueueItem] = (),
        request_context: RequestContext | None = None,
    ) -> CustomerDashboardComposition:
        """Build the complete dashboard projection for one tenant/user scope."""
        if kpis.tenant_id != tenant_id:
            raise ValueError("Dashboard KPIs do not match tenant")

        foundation = CustomerDashboardFoundationService.build(
            tenant_id=tenant_id,
            user_id=user_id,
            sections=(),
            request_context=request_context,
        )

        kpi_sections = kpis.as_dashboard_sections()
        queue = tuple(work_queue)
        queue_section = CustomerDashboardSection(
            "work_queue_items",
            "Work Queue",
            (
                CustomerDashboardMetric(
                    "total_work_items",
                    "Total Work Items",
                    DashboardMetricKind.COUNT,
                    len(queue),
                ),
                CustomerDashboardMetric(
                    "due_or_overdue_work_items",
                    "Due or Overdue",
                    DashboardMetricKind.COUNT,
                    sum(item.due_at <= item_reference for item in queue for item_reference in (max((item.due_at for item in queue), default=datetime.min),)),
                ),
            ),
        )
        sections = tuple(kpi_sections) + (queue_section,)

        return CustomerDashboardComposition(
            foundation=foundation,
            kpis=kpis,
            work_queue=queue,
            sections=sections,
        )
