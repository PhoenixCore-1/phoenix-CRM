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
from phoenix_crm.services.customer_call_follow_up_queue import (
    CRMWorkItemType,
    CRMWorkQueueItem,
    CustomerCallFollowUpQueueService,
)


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
        reference_at: datetime,
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

        queue = tuple(work_queue)
        overdue = CustomerCallFollowUpQueueService.overdue(queue, reference_at=reference_at)
        due_or_overdue = CustomerCallFollowUpQueueService.due_or_overdue(
            queue, reference_at=reference_at
        )
        call_count = sum(item.item_type is CRMWorkItemType.CALL for item in queue)
        follow_up_count = sum(item.item_type is CRMWorkItemType.FOLLOW_UP for item in queue)

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
                    len(due_or_overdue),
                ),
                CustomerDashboardMetric(
                    "overdue_work_items",
                    "Overdue",
                    DashboardMetricKind.COUNT,
                    len(overdue),
                ),
                CustomerDashboardMetric(
                    "call_work_items",
                    "Calls",
                    DashboardMetricKind.COUNT,
                    call_count,
                ),
                CustomerDashboardMetric(
                    "follow_up_work_items",
                    "Follow-ups",
                    DashboardMetricKind.COUNT,
                    follow_up_count,
                ),
            ),
        )
        sections = tuple(kpis.as_dashboard_sections()) + (queue_section,)

        return CustomerDashboardComposition(
            foundation=foundation,
            kpis=kpis,
            work_queue=queue,
            sections=sections,
        )
