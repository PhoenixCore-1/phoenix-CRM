from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import (
    ActivityType,
    Customer,
    CustomerActivity,
    CustomerFollowUp,
    CustomerPotential,
    CustomerSolution,
    FollowUpStatus,
    PotentialSource,
    PotentialStatus,
    SolutionRelationship,
)
from phoenix_crm.services import Customer360OverviewService
from phoenix_crm.services.customer_360_contract import Customer360View


def make_customer(tenant_id, customer_id=None):
    return Customer(
        tenant_id=tenant_id,
        name="Acme",
        customer_type_id=uuid4(),
        call_class_id=uuid4(),
        id=customer_id or uuid4(),
    )


def make_view(customer):
    return Customer360View.from_customer(customer)


def context_for(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_overview_builds_core_customer_counts():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    activities = [
        CustomerActivity(
            tenant_id=tenant_id,
            customer_id=customer.id,
            activity_type=ActivityType.CALL,
            subject="Call",
            occurred_at=datetime.now(timezone.utc),
        )
    ]
    follow_up = CustomerFollowUp(
        tenant_id=tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=uuid4(),
        due_at=datetime.now(timezone.utc) + timedelta(days=1),
        reason="Follow up",
    )
    potential = CustomerPotential(
        tenant_id=tenant_id,
        customer_id=customer.id,
        solution_name="Anchors",
        reason="Customer need",
        source=PotentialSource.MANUAL_ENTRY,
    )
    current = CustomerSolution(
        tenant_id=tenant_id,
        customer_id=customer.id,
        solution_name="Existing",
        relationship=SolutionRelationship.CURRENT,
    )
    possible = CustomerSolution(
        tenant_id=tenant_id,
        customer_id=customer.id,
        solution_name="Potential",
        relationship=SolutionRelationship.POTENTIAL,
    )

    overview = Customer360OverviewService.build(
        customer=customer,
        view=make_view(customer),
        activities=activities,
        follow_ups=[follow_up],
        potentials=[potential],
        solutions=[current, possible],
    )

    assert overview.activity_count == 1
    assert overview.open_follow_up_count == 1
    assert overview.overdue_follow_up_count == 0
    assert overview.active_potential_count == 1
    assert overview.current_solution_count == 1
    assert overview.potential_solution_count == 1
    assert overview.last_activity_at == activities[0].occurred_at


def test_overview_excludes_other_tenant_and_customer_records():
    tenant_id = uuid4()
    other_tenant = uuid4()
    customer = make_customer(tenant_id)
    other_customer = make_customer(tenant_id)

    activity = CustomerActivity(
        tenant_id=other_tenant,
        customer_id=customer.id,
        activity_type=ActivityType.CALL,
        subject="Other tenant",
        occurred_at=datetime.now(timezone.utc),
    )
    other_activity = CustomerActivity(
        tenant_id=tenant_id,
        customer_id=other_customer.id,
        activity_type=ActivityType.CALL,
        subject="Other customer",
        occurred_at=datetime.now(timezone.utc),
    )

    overview = Customer360OverviewService.build(
        customer=customer,
        view=make_view(customer),
        activities=[activity, other_activity],
    )

    assert overview.activity_count == 0
    assert overview.last_activity_at is None


def test_overview_counts_only_open_follow_ups():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    now = datetime.now(timezone.utc)
    completed = CustomerFollowUp(
        tenant_id=tenant_id, customer_id=customer.id, assigned_to_user_id=uuid4(),
        due_at=now - timedelta(days=1), reason="Done", status=FollowUpStatus.COMPLETED,
    )
    planned = CustomerFollowUp(
        tenant_id=tenant_id, customer_id=customer.id, assigned_to_user_id=uuid4(),
        due_at=now + timedelta(days=1), reason="Open",
    )

    overview = Customer360OverviewService.build(
        customer=customer, view=make_view(customer), follow_ups=[completed, planned]
    )

    assert overview.open_follow_up_count == 1
    assert overview.overdue_follow_up_count == 0


def test_overview_counts_overdue_open_follow_ups():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    overdue = CustomerFollowUp(
        tenant_id=tenant_id,
        customer_id=customer.id,
        assigned_to_user_id=uuid4(),
        due_at=datetime.now(timezone.utc) - timedelta(days=1),
        reason="Overdue",
    )

    overview = Customer360OverviewService.build(
        customer=customer, view=make_view(customer), follow_ups=[overdue]
    )

    assert overview.open_follow_up_count == 1
    assert overview.overdue_follow_up_count == 1


def test_overview_counts_only_active_potentials():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    active = CustomerPotential(
        tenant_id=tenant_id, customer_id=customer.id, solution_name="A",
        reason="Need", source=PotentialSource.MANUAL_ENTRY,
    )
    declined = CustomerPotential(
        tenant_id=tenant_id, customer_id=customer.id, solution_name="B",
        reason="No need", source=PotentialSource.MANUAL_ENTRY,
        status=PotentialStatus.DECLINED,
    )

    overview = Customer360OverviewService.build(
        customer=customer, view=make_view(customer), potentials=[active, declined]
    )

    assert overview.active_potential_count == 1


def test_overview_counts_active_current_and_potential_solutions():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    current = CustomerSolution(
        tenant_id=tenant_id, customer_id=customer.id, solution_name="Current",
        relationship=SolutionRelationship.CURRENT,
    )
    potential = CustomerSolution(
        tenant_id=tenant_id, customer_id=customer.id, solution_name="Potential",
        relationship=SolutionRelationship.POTENTIAL,
    )

    overview = Customer360OverviewService.build(
        customer=customer, view=make_view(customer), solutions=[current, potential]
    )

    assert overview.current_solution_count == 1
    assert overview.potential_solution_count == 1


def test_overview_requires_matching_customer_view():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    other = make_customer(tenant_id)

    with pytest.raises(ValueError):
        Customer360OverviewService.build(customer=customer, view=make_view(other))


def test_overview_enforces_core_access_scope():
    tenant_id = uuid4()
    customer = make_customer(tenant_id)
    context = context_for(tenant_id, uuid4())

    with pytest.raises(PermissionError):
        Customer360OverviewService.build(
            customer=customer, view=make_view(customer), request_context=context
        )
