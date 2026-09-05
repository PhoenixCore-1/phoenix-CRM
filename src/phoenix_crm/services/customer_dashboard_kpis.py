"""CRM dashboard KPI definitions and calculations for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import (
    Customer,
    CustomerActivity,
    CustomerCallClass,
    CustomerFollowUp,
    CustomerPotential,
    CustomerStatus,
    FollowUpStatus,
    Lead,
    LeadStatus,
    PotentialStatus,
)
from phoenix_crm.services.customer_360_dashboard import (
    CustomerDashboardMetric,
    CustomerDashboardSection,
    DashboardMetricKind,
)
from phoenix_crm.services.call_cadence import CallCadenceService


@dataclass(frozen=True, slots=True)
class CRMKPISet:
    """Immutable authoritative CRM dashboard KPI values."""

    total_customers: int
    active_customers: int
    calls_due: int
    overdue_follow_ups: int
    open_follow_ups: int
    new_leads: int
    potential_customers: int
    active_potential: int
    recent_activity: int
    customer_type_counts: tuple[tuple[str, int], ...]
    call_class_counts: tuple[tuple[str, int], ...]

    def metrics(self) -> tuple[CustomerDashboardMetric, ...]:
        return (
            CustomerDashboardMetric("total_customers", "Total Customers", DashboardMetricKind.COUNT, self.total_customers),
            CustomerDashboardMetric("active_customers", "Active Customers", DashboardMetricKind.COUNT, self.active_customers),
            CustomerDashboardMetric("calls_due", "Calls Due", DashboardMetricKind.COUNT, self.calls_due),
            CustomerDashboardMetric("overdue_follow_ups", "Overdue Follow-ups", DashboardMetricKind.COUNT, self.overdue_follow_ups),
            CustomerDashboardMetric("open_follow_ups", "Open Follow-ups", DashboardMetricKind.COUNT, self.open_follow_ups),
            CustomerDashboardMetric("new_leads", "New Leads", DashboardMetricKind.COUNT, self.new_leads),
            CustomerDashboardMetric("potential_customers", "Potential Customers", DashboardMetricKind.COUNT, self.potential_customers),
            CustomerDashboardMetric("active_potential", "Active Potential", DashboardMetricKind.COUNT, self.active_potential),
            CustomerDashboardMetric("recent_activity", "Recent Activity", DashboardMetricKind.COUNT, self.recent_activity),
        )


class CRMKPIService:
    """Calculate CRM-owned dashboard KPIs from supplied domain records."""

    ACTIVE_CUSTOMER_STATUSES = frozenset({CustomerStatus.ACTIVE})
    OPEN_FOLLOW_UP_STATUSES = frozenset({FollowUpStatus.PLANNED, FollowUpStatus.DUE, FollowUpStatus.RESCHEDULED})
    ACTIVE_POTENTIAL_STATUSES = frozenset({PotentialStatus.IDENTIFIED, PotentialStatus.QUALIFYING, PotentialStatus.QUALIFIED})

    @staticmethod
    def calculate(
        *,
        tenant_id: UUID,
        customers: tuple[Customer, ...] = (),
        leads: tuple[Lead, ...] = (),
        activities: tuple[CustomerActivity, ...] = (),
        follow_ups: tuple[CustomerFollowUp, ...] = (),
        potentials: tuple[CustomerPotential, ...] = (),
        call_classes: tuple[CustomerCallClass, ...] = (),
        reference_at: datetime,
        recent_activity_since: datetime | None = None,
        request_context: RequestContext | None = None,
    ) -> CRMKPISet:
        CRMKPIService._require_access(tenant_id=tenant_id, request_context=request_context)

        tenant_customers = tuple(item for item in customers if item.tenant_id == tenant_id)
        customer_ids = {item.id for item in tenant_customers}
        tenant_leads = tuple(item for item in leads if item.tenant_id == tenant_id)
        tenant_activities = tuple(
            item for item in activities
            if item.tenant_id == tenant_id and item.customer_id in customer_ids
        )
        tenant_follow_ups = tuple(
            item for item in follow_ups
            if item.tenant_id == tenant_id and item.customer_id in customer_ids
        )
        tenant_potentials = tuple(
            item for item in potentials
            if item.tenant_id == tenant_id and item.customer_id in customer_ids
        )
        class_by_id = {item.id: item for item in call_classes}

        calls_due = 0
        for customer in tenant_customers:
            call_class = class_by_id.get(customer.call_class_id)
            if call_class is None:
                continue
            cadence = CallCadenceService.resolve(
                customer,
                call_class,
                list(tenant_activities),
                reference_at=reference_at,
            )
            if cadence.next_interaction_at is not None and cadence.next_interaction_at <= reference_at:
                calls_due += 1

        open_follow_ups = tuple(
            item for item in tenant_follow_ups if item.status in CRMKPIService.OPEN_FOLLOW_UP_STATUSES
        )
        overdue_follow_ups = tuple(item for item in open_follow_ups if item.due_at <= reference_at)
        active_potential = tuple(
            item for item in tenant_potentials if item.status in CRMKPIService.ACTIVE_POTENTIAL_STATUSES
        )
        recent_activity = (
            tuple(item for item in tenant_activities if item.occurred_at >= recent_activity_since)
            if recent_activity_since is not None
            else tenant_activities
        )

        customer_type_counts = CRMKPIService._counts(
            ((str(customer.customer_type_id), 1) for customer in tenant_customers)
        )
        call_class_counts = CRMKPIService._counts(
            ((str(customer.call_class_id), 1) for customer in tenant_customers)
        )

        return CRMKPISet(
            total_customers=len(tenant_customers),
            active_customers=sum(item.status in CRMKPIService.ACTIVE_CUSTOMER_STATUSES for item in tenant_customers),
            calls_due=calls_due,
            overdue_follow_ups=len(overdue_follow_ups),
            open_follow_ups=len(open_follow_ups),
            new_leads=sum(item.status is LeadStatus.NEW for item in tenant_leads),
            potential_customers=sum(item.status is LeadStatus.POTENTIAL_CUSTOMER for item in tenant_leads),
            active_potential=len(active_potential),
            recent_activity=len(recent_activity),
            customer_type_counts=customer_type_counts,
            call_class_counts=call_class_counts,
        )

    @staticmethod
    def dashboard_section(kpis: CRMKPISet) -> CustomerDashboardSection:
        """Expose the KPI set through the frozen dashboard foundation contract."""
        return CustomerDashboardSection(
            key="crm_kpis",
            label="CRM KPIs",
            metrics=kpis.metrics(),
        )

    @staticmethod
    def _counts(values: object) -> tuple[tuple[str, int], ...]:
        counts: dict[str, int] = {}
        for key, amount in values:  # type: ignore[misc]
            counts[key] = counts.get(key, 0) + amount
        return tuple(sorted(counts.items(), key=lambda item: item[0]))

    @staticmethod
    def _require_access(*, tenant_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this tenant")
