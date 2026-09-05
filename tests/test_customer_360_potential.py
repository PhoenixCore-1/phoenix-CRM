from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import (
    CustomerPotential,
    CustomerSolution,
    PotentialPriority,
    PotentialSource,
    PotentialStatus,
    SolutionRelationship,
)
from phoenix_crm.services import Customer360PotentialService


def context(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def potential(tenant_id, customer_id, name, status=PotentialStatus.IDENTIFIED, priority=PotentialPriority.NORMAL):
    return CustomerPotential(
        tenant_id=tenant_id,
        customer_id=customer_id,
        solution_name=name,
        reason="Customer need identified",
        source=PotentialSource.CUSTOMER_ACTIVITY,
        status=status,
        priority=priority,
    )


def test_build_separates_active_potentials_and_solution_relationships():
    tenant_id, customer_id = uuid4(), uuid4()
    potentials = (
        potential(tenant_id, customer_id, "Chemical anchor", PotentialStatus.QUALIFIED, PotentialPriority.HIGH),
        potential(tenant_id, customer_id, "Timber screw"),
        potential(tenant_id, customer_id, "Closed solution", PotentialStatus.CLOSED),
    )
    solutions = (
        CustomerSolution(tenant_id, customer_id, "Mechanical anchor", SolutionRelationship.CURRENT),
        CustomerSolution(tenant_id, customer_id, "Chemical anchor", SolutionRelationship.POTENTIAL),
    )
    section = Customer360PotentialService.build(
        tenant_id=tenant_id, customer_id=customer_id, potentials=potentials, solutions=solutions
    )
    assert section.active_potential_count == 2
    assert section.qualified_potential_count == 1
    assert section.high_priority_potential_count == 1
    assert [item.solution_name for item in section.current_solutions] == ["Mechanical anchor"]
    assert [item.solution_name for item in section.potential_solutions] == ["Chemical anchor"]


def test_build_filters_other_tenant_and_customer_records():
    tenant_id, customer_id = uuid4(), uuid4()
    potentials = (
        potential(tenant_id, customer_id, "Valid"),
        potential(uuid4(), customer_id, "Other tenant"),
        potential(tenant_id, uuid4(), "Other customer"),
    )
    section = Customer360PotentialService.build(
        tenant_id=tenant_id, customer_id=customer_id, potentials=potentials
    )
    assert [item.solution_name for item in section.potentials] == ["Valid"]


def test_build_enforces_core_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(PermissionError):
        Customer360PotentialService.build(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=context(tenant_id, uuid4()),
        )


def test_build_returns_empty_section_for_no_records():
    tenant_id, customer_id = uuid4(), uuid4()
    section = Customer360PotentialService.build(tenant_id=tenant_id, customer_id=customer_id)
    assert section.active_potential_count == 0
    assert section.qualified_potential_count == 0
    assert section.high_priority_potential_count == 0
    assert section.potentials == ()
    assert section.current_solutions == ()
    assert section.potential_solutions == ()


def test_build_does_not_expose_terminal_potentials_or_inactive_solutions():
    tenant_id, customer_id = uuid4(), uuid4()
    potentials = (potential(tenant_id, customer_id, "Closed", PotentialStatus.CLOSED),)
    inactive = CustomerSolution(tenant_id, customer_id, "Old", SolutionRelationship.CURRENT)
    inactive.mark_inactive()
    section = Customer360PotentialService.build(
        tenant_id=tenant_id, customer_id=customer_id, potentials=potentials, solutions=(inactive,)
    )
    assert section.potentials == ()
    assert section.current_solutions == ()


def test_build_does_not_create_or_modify_domain_objects():
    tenant_id, customer_id = uuid4(), uuid4()
    item = potential(tenant_id, customer_id, "Anchor")
    solution = CustomerSolution(tenant_id, customer_id, "Anchor", SolutionRelationship.CURRENT)
    original_status = item.status
    original_solution_status = solution.status
    Customer360PotentialService.build(
        tenant_id=tenant_id, customer_id=customer_id, potentials=(item,), solutions=(solution,)
    )
    assert item.status is original_status
    assert solution.status is original_solution_status
