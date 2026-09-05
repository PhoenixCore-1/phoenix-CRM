"""Tests for the Phase 10.1 CRM dashboard foundation."""

from uuid import uuid4

import pytest

from phoenix_crm.api import RequestContext
from phoenix_crm.services import (
    CustomerDashboardFoundationService,
    CustomerDashboardMetric,
    CustomerDashboardSection,
    DashboardMetricKind,
)


def test_build_preserves_immutable_dashboard_structure():
    tenant_id = uuid4()
    user_id = uuid4()
    section = CustomerDashboardSection(
        key="customer_activity",
        label="Customer Activity",
        metrics=(
            CustomerDashboardMetric("activity_count", "Activities", DashboardMetricKind.COUNT, 4),
            CustomerDashboardMetric("last_activity", "Last Activity", DashboardMetricKind.DATE, "2026-09-05T09:00:00+00:00"),
        ),
    )

    dashboard = CustomerDashboardFoundationService.build(
        tenant_id=tenant_id,
        user_id=user_id,
        sections=(section,),
    )

    assert dashboard.tenant_id == tenant_id
    assert dashboard.user_id == user_id
    assert dashboard.section_keys == ("customer_activity",)
    assert dashboard.sections[0].metrics[0].value == 4


def test_empty_optional_dashboard_is_valid():
    dashboard = CustomerDashboardFoundationService.build(
        tenant_id=uuid4(),
        user_id=uuid4(),
    )

    assert dashboard.sections == ()
    assert dashboard.section_keys == ()


def test_duplicate_section_keys_are_rejected():
    section = CustomerDashboardSection("activity", "Activity")

    with pytest.raises(ValueError, match="duplicate dashboard section key"):
        CustomerDashboardFoundationService.build(
            tenant_id=uuid4(),
            user_id=uuid4(),
            sections=(section, section),
        )


def test_duplicate_metric_keys_are_rejected_within_section():
    section = CustomerDashboardSection(
        "activity",
        "Activity",
        (
            CustomerDashboardMetric("count", "Count", DashboardMetricKind.COUNT, 1),
            CustomerDashboardMetric("count", "Count Again", DashboardMetricKind.COUNT, 2),
        ),
    )

    with pytest.raises(ValueError, match="duplicate dashboard metric key"):
        CustomerDashboardFoundationService.build(
            tenant_id=uuid4(),
            user_id=uuid4(),
            sections=(section,),
        )


def test_core_tenant_scope_is_enforced():
    tenant_id = uuid4()
    context = RequestContext.for_tenant(str(uuid4()))

    with pytest.raises(PermissionError, match="tenant"):
        CustomerDashboardFoundationService.build(
            tenant_id=tenant_id,
            user_id=uuid4(),
            request_context=context,
        )


def test_unavailable_sections_are_preserved_for_graceful_degradation():
    section = CustomerDashboardSection(
        key="projects",
        label="Projects",
        available=False,
    )

    dashboard = CustomerDashboardFoundationService.build(
        tenant_id=uuid4(),
        user_id=uuid4(),
        sections=(section,),
    )

    assert dashboard.sections[0].available is False
    assert dashboard.sections[0].metrics == ()


def test_dashboard_is_read_only():
    dashboard = CustomerDashboardFoundationService.build(
        tenant_id=uuid4(),
        user_id=uuid4(),
        sections=(CustomerDashboardSection("activity", "Activity"),),
    )

    with pytest.raises(AttributeError):
        dashboard.sections = ()  # type: ignore[misc]
