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
class CustomerDashboardKPIs:
    """Immutable CRM-owned KPI snapshot for one tenant and access scope."""

    tenant_id: UUID
    total_customers: int
    active_customers: int
    prospect_customers: int
    on_hold_customers: int
    inactive_customers: int
    closed_customers: int
    new_leads: int
    potential_customers: int
    active_potential: int
    open_follow_ups: int
    overdue_follow_ups: int
    calls_due: int
    recent_activities: int
    customers_by_type: tuple[tuple[str, int], ...]
    customers_by_call_class: tuple[tuple[str, int], ...]

    def as_dashboard_sections(self) -> tuple[CustomerDashboardSection, ...]:
        """Render the KPI snapshot through the Phase 10.1 dashboard contract."""
        customer_metrics = (
            CustomerDashboardMetric("total_customers", "Total Customers", DashboardMetricKind.COUNT, self.total_customers),
            CustomerDashboardMetric("active_customers", "Active Customers", DashboardMetricKind.COUNT, self.active_customers),
            CustomerDashboardMetric("prospect_customers", "Prospects", DashboardMetricKind.COUNT, self.prospect_customers),
            CustomerDashboardMetric("on_hold_customers", "On Hold", DashboardMetricKind.COUNT, self.on_hold_customers),
        )
        work_metrics = (
            CustomerDashboardMetric("calls_due", "Calls Due", DashboardMetricKind.COUNT, self.calls_due),
            CustomerDashboardMetric("open_follow_ups", "Open Follow-ups", DashboardMetricKind.COUNT, self.open_follow_ups),
            CustomerDashboardMetric("overdue_follow_ups", "Overdue Follow-ups", DashboardMetricKind.COUNT, self.overdue_follow_ups),
            CustomerDashboardMetric("recent_activities", "Recent Activities", DashboardMetricKind.COUNT, self.recent_activities),
        )
        lead_metrics = (
            CustomerDashboardMetric("new_leads", "New Leads", DashboardMetricKind.COUNT, self.new_leads),
            CustomerDashboardMetric("potential_customers", "Potential Customers", DashboardMetricKind.COUNT, self.potential_customers),
            CustomerDashboardMetric("active_potential", "Active Potential", DashboardMetricKind.COUNT, self.active_potential),
        )
        return (
            CustomerDashboardSection("customers", "Customers", customer_metrics),
            CustomerDashboardSection("work_queue", "Relationship Work", work_metrics),
            CustomerDashboardSection("leads_and_potential", "Leads & Potential", lead_metrics),
        )


class CustomerDashboardKPIService:
    """Calculate CRM KPIs from supplied CRM-owned records only."""

    ACTIVE_POTENTIAL_STATUSES = frozenset({
        PotentialStatus.IDENTIFIED,
        PotentialStatus.QUALIFYING,
        PotentialStatus.QUALIFIED,
    })
    OPEN_FOLLOW_UP_STATUSES = frozenset({FollowUpStatus.PLANNED, FollowUpStatus.DUE})

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customers: tuple[Customer, ...] | list[Customer] = (),
        leads: tuple[Lead, ...] | list[Lead] = (),
        potentials: tuple[CustomerPotential, ...] | list[CustomerPotential] = (),
        follow_ups: tuple[CustomerFollowUp, ...] | list[CustomerFollowUp] = (),
        activities: tuple[CustomerActivity, ...] | list[CustomerActivity] = (),
        customer_types: tuple[object, ...] | list[object] = (),
        call_classes: tuple[CustomerCallClass, ...] | list[CustomerCallClass] = (),
        reference_at: datetime,
        recent_activity_days: int = 30,
        request_context: RequestContext | None = None,
    ) -> CustomerDashboardKPIs:
        """Build a deterministic tenant/access-scoped CRM KPI snapshot."""
        if recent_activity_days <= 0:
            raise ValueError("recent_activity_days must be positive")
        if request_context is not None and request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this tenant")

        scoped_customers = tuple(
            item for item in customers
            if item.tenant_id == tenant_id and CustomerDashboardKPIService._accessible(item.id, request_context)
        )
        customer_ids = {item.id for item in scoped_customers}

        scoped_leads = tuple(item for item in leads if item.tenant_id == tenant_id and CustomerDashboardKPIService._accessible(item.id, request_context))
        scoped_potentials = tuple(item for item in potentials if item.tenant_id == tenant_id and item.customer_id in customer_ids)
        scoped_follow_ups = tuple(item for item in follow_ups if item.tenant_id == tenant_id and item.customer_id in customer_ids)
        scoped_activities = tuple(item for item in activities if item.tenant_id == tenant_id and item.customer_id in customer_ids)

        open_follow_ups = tuple(item for item in scoped_follow_ups if item.status in CustomerDashboardKPIService.OPEN_FOLLOW_UP_STATUSES)
        overdue_follow_ups = tuple(item for item in open_follow_ups if item.due_at < reference_at)
        active_potential = tuple(item for item in scoped_potentials if item.status in CustomerDashboardKPIService.ACTIVE_POTENTIAL_STATUSES)
        recent_cutoff = reference_at.timestamp() - recent_activity_days * 86400
        recent_activities = tuple(item for item in scoped_activities if item.occurred_at.timestamp() >= recent_cutoff and item.occurred_at <= reference_at)

        calls_due = CustomerDashboardKPIService._calls_due(
            scoped_customers, scoped_activities, scoped_follow_ups, call_classes, reference_at
        )

        type_names = {getattr(item, "id", None): getattr(item, "name", str(getattr(item, "id", ""))) for item in customer_types}
        class_names = {item.id: item.name for item in call_classes}

        return CustomerDashboardKPIs(
            tenant_id=tenant_id,
            total_customers=len(scoped_customers),
            active_customers=sum(item.status is CustomerStatus.ACTIVE for item in scoped_customers),
            prospect_customers=sum(item.status is CustomerStatus.PROSPECT for item in scoped_customers),
            on_hold_customers=sum(item.status is CustomerStatus.ON_HOLD for item in scoped_customers),
            inactive_customers=sum(item.status is CustomerStatus.INACTIVE for item in scoped_customers),
            closed_customers=sum(item.status is CustomerStatus.CLOSED for item in scoped_customers),
            new_leads=sum(item.status is LeadStatus.NEW for item in scoped_leads),
            potential_customers=sum(item.status is LeadStatus.POTENTIAL_CUSTOMER for item in scoped_leads),
            active_potential=len(active_potential),
            open_follow_ups=len(open_follow_ups),
            overdue_follow_ups=len(overdue_follow_ups),
            calls_due=calls_due,
            recent_activities=len(recent_activities),
            customers_by_type=CustomerDashboardKPIService._distribution(scoped_customers, lambda item: type_names.get(item.customer_type_id, str(item.customer_type_id))),
            customers_by_call_class=CustomerDashboardKPIService._distribution(scoped_customers, lambda item: class_names.get(item.call_class_id, str(item.call_class_id))),
        )

    @staticmethod
    def _accessible(resource_id: UUID, request_context: RequestContext | None) -> bool:
        return request_context is None or request_context.can_access_resource(str(resource_id))

    @staticmethod
    def _distribution(items: tuple[Customer, ...], label_for) -> tuple[tuple[str, int], ...]:
        counts: dict[str, int] = {}
        for item in items:
            label = str(label_for(item))
            counts[label] = counts.get(label, 0) + 1
        return tuple(sorted(counts.items(), key=lambda pair: (pair[0].lower(), pair[0])))

    @staticmethod
    def _calls_due(
        customers: tuple[Customer, ...],
        activities: tuple[CustomerActivity, ...],
        follow_ups: tuple[CustomerFollowUp, ...],
        call_classes: tuple[CustomerCallClass, ...] | list[CustomerCallClass],
        reference_at: datetime,
    ) -> int:
        classes = {item.id: item for item in call_classes}
        due = 0
        for customer in customers:
            call_class = classes.get(customer.call_class_id)
            if call_class is None:
                continue
            cadence = CallCadenceService.resolve(customer, call_class, list(activities), reference_at=reference_at)
            if cadence.next_interaction_at is not None and cadence.next_interaction_at <= reference_at:
                due += 1
        due += sum(item.due_at <= reference_at for item in follow_ups if item.status in CustomerDashboardKPIService.OPEN_FOLLOW_UP_STATUSES)
        return due
