"""Deterministic, tenant-scoped CRM reporting contracts for Phase 12."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Customer, CustomerActivity, CustomerFollowUp, CustomerStatus, FollowUpStatus


@dataclass(frozen=True, slots=True)
class CRMReportSnapshot:
    """Immutable operational report snapshot for one tenant and access scope."""

    tenant_id: UUID
    generated_at: datetime
    total_customers: int
    active_customers: int
    prospect_customers: int
    inactive_customers: int
    on_hold_customers: int
    closed_customers: int
    open_follow_ups: int
    overdue_follow_ups: int
    recent_activities: int


class CRMReportingService:
    """Build read-only CRM operational reporting from supplied records."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        reference_at: datetime,
        customers: tuple[Customer, ...] | list[Customer] = (),
        follow_ups: tuple[CustomerFollowUp, ...] | list[CustomerFollowUp] = (),
        activities: tuple[CustomerActivity, ...] | list[CustomerActivity] = (),
        recent_activity_days: int = 30,
        request_context: RequestContext | None = None,
    ) -> CRMReportSnapshot:
        if recent_activity_days <= 0:
            raise ValueError("recent_activity_days must be positive")
        if request_context is not None and request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this tenant")

        scoped_customers = tuple(
            item for item in customers
            if item.tenant_id == tenant_id
            and (request_context is None or request_context.can_access_resource(str(item.id)))
        )
        customer_ids = {item.id for item in scoped_customers}
        scoped_follow_ups = tuple(
            item for item in follow_ups
            if item.tenant_id == tenant_id and item.customer_id in customer_ids
        )
        scoped_activities = tuple(
            item for item in activities
            if item.tenant_id == tenant_id
            and item.customer_id in customer_ids
            and item.occurred_at <= reference_at
        )
        open_follow_ups = tuple(
            item for item in scoped_follow_ups
            if item.status in {FollowUpStatus.PLANNED, FollowUpStatus.DUE}
        )
        cutoff = reference_at.timestamp() - recent_activity_days * 86400
        recent = tuple(item for item in scoped_activities if item.occurred_at.timestamp() >= cutoff)

        return CRMReportSnapshot(
            tenant_id=tenant_id,
            generated_at=reference_at,
            total_customers=len(scoped_customers),
            active_customers=sum(item.status is CustomerStatus.ACTIVE for item in scoped_customers),
            prospect_customers=sum(item.status is CustomerStatus.PROSPECT for item in scoped_customers),
            inactive_customers=sum(item.status is CustomerStatus.INACTIVE for item in scoped_customers),
            on_hold_customers=sum(item.status is CustomerStatus.ON_HOLD for item in scoped_customers),
            closed_customers=sum(item.status is CustomerStatus.CLOSED for item in scoped_customers),
            open_follow_ups=len(open_follow_ups),
            overdue_follow_ups=sum(item.due_at < reference_at for item in open_follow_ups),
            recent_activities=len(recent),
        )
