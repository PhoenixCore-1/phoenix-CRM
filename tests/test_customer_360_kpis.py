"""Tests for the Phase 10.2 CRM KPI definitions and calculations."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import (
    ActivityType,
    CallCadence,
    Customer,
    CustomerActivity,
    CustomerCallClass,
    CustomerPotential,
    CustomerStatus,
    CustomerType,
    FollowUpStatus,
    FollowUpPriority,
    CustomerFollowUp,
    Lead,
    LeadSource,
    LeadStatus,
    PotentialSource,
)
from phoenix_crm.services import CustomerDashboardKPIService


def _customer(tenant_id, *, name="Acme", status=CustomerStatus.ACTIVE, type_id=None, class_id=None):
    return Customer(
        tenant_id=tenant_id,
        name=name,
        customer_type_id=type_id or uuid4(),
        call_class_id=class_id or uuid4(),
        status=status,
    )


def test_calculates_customer_lead_potential_follow_up_and_activity_kpis():
    tenant_id = uuid4()
    reference_at = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)
    customer = _customer(tenant_id)
    prospect = _customer(tenant_id, name="Prospect", status=CustomerStatus.PROSPECT)
    lead_new = Lead(tenant_id=tenant_id, name="New Lead", source=LeadSource.WEBSITE)
    lead_potential = Lead(tenant_id=tenant_id, name="Potential", source=LeadSource.REFERRAL, status=LeadStatus.POTENTIAL_CUSTOMER)
    potential = CustomerPotential(
        tenant_id=tenant_id,
        customer_id=customer.id,
        solution_name="Chemical Anchor",
        reason="Observed application gap",
        source=PotentialSource.CUSTOMER_ACTIVITY,
    )
    follow_up = CustomerFollowUp(
        tenant_id=tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=uuid4(),
        due_at=reference_at - timedelta(days=1),
        reason="Call customer",
        status=FollowUpStatus.DUE,
    )
    activity = CustomerActivity(
        tenant_id=tenant_id,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Customer call",
        occurred_at=reference_at - timedelta(days=2),
    )

    kpis = CustomerDashboardKPIService.build(
        tenant_id=tenant_id,
        customers=(customer, prospect),
        leads=(lead_new, lead_potential),
        potentials=(potential,),
        follow_ups=(follow_up,),
        activities=(activity,),
        reference_at=reference_at,
    )

    assert kpis.total_customers == 2
    assert kpis.active_customers == 1
    assert kpis.prospect_customers == 1
    assert kpis.new_leads == 1
    assert kpis.potential_customers == 1
    assert kpis.active_potential == 1
    assert kpis.open_follow_ups == 1
    assert kpis.overdue_follow_ups == 1
    assert kpis.recent_activities == 1
    assert kpis.calls_due == 1


def test_tenant_isolation_excludes_other_tenant_records():
    tenant_id = uuid4()
    other_tenant = uuid4()
    customer = _customer(tenant_id)
    other_customer = _customer(other_tenant)
    lead = Lead(tenant_id=other_tenant, name="Other", source=LeadSource.WEBSITE)

    kpis = CustomerDashboardKPIService.build(
        tenant_id=tenant_id,
        customers=(customer, other_customer),
        leads=(lead,),
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )

    assert kpis.total_customers == 1
    assert kpis.new_leads == 0


def test_core_access_scope_limits_customer_metrics():
    tenant_id = uuid4()
    allowed = _customer(tenant_id, name="Allowed")
    denied = _customer(tenant_id, name="Denied")
    context = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(allowed.id)})),
    )

    kpis = CustomerDashboardKPIService.build(
        tenant_id=tenant_id,
        customers=(allowed, denied),
        request_context=context,
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )

    assert kpis.total_customers == 1
    assert kpis.customers_by_type


def test_core_tenant_scope_is_enforced():
    tenant_id = uuid4()
    context = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
    )

    with pytest.raises(PermissionError, match="tenant"):
        CustomerDashboardKPIService.build(
            tenant_id=tenant_id,
            request_context=context,
            reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        )


def test_customer_distributions_are_deterministic_and_named():
    tenant_id = uuid4()
    type_a = CustomerType(uuid4(), "Builder", "builder")
    type_b = CustomerType(uuid4(), "Architect", "architect")
    class_a = CustomerCallClass(uuid4(), "B", "B", CallCadence(14))
    class_b = CustomerCallClass(uuid4(), "A", "A", CallCadence(7))
    customers = (
        _customer(tenant_id, name="One", type_id=type_a.id, class_id=class_a.id),
        _customer(tenant_id, name="Two", type_id=type_b.id, class_id=class_b.id),
        _customer(tenant_id, name="Three", type_id=type_a.id, class_id=class_a.id),
    )

    kpis = CustomerDashboardKPIService.build(
        tenant_id=tenant_id,
        customers=customers,
        customer_types=(type_a, type_b),
        call_classes=(class_a, class_b),
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )

    assert kpis.customers_by_type == (("Architect", 1), ("Builder", 2))
    assert kpis.customers_by_call_class == (("A", 1), ("B", 2))


def test_invalid_recent_activity_window_is_rejected():
    with pytest.raises(ValueError, match="recent_activity_days"):
        CustomerDashboardKPIService.build(
            tenant_id=uuid4(),
            reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
            recent_activity_days=0,
        )


def test_dashboard_sections_use_the_frozen_10_1_contract():
    kpis = CustomerDashboardKPIService.build(
        tenant_id=uuid4(),
        reference_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )

    sections = kpis.as_dashboard_sections()

    assert tuple(section.key for section in sections) == (
        "customers",
        "work_queue",
        "leads_and_potential",
    )
    assert sections[0].metrics[0].key == "total_customers"
    assert sections[1].metrics[0].key == "calls_due"
    assert sections[2].metrics[0].key == "new_leads"
