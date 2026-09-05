"""Tests for Phase 5.5 call planning foundation."""

from datetime import datetime, timezone
from uuid import uuid4

from phoenix_crm.domain import (
    ActivityType,
    CallCadence,
    Customer,
    CustomerActivity,
    CustomerCallClass,
    CustomerFollowUp,
)
from phoenix_crm.services import CallPlanItemType, CallPlanningService

REFERENCE = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)


def customer(days=7):
    c = Customer(uuid4(), "Acme", uuid4(), uuid4())
    return c, CustomerCallClass(c.call_class_id, "A Weekly", "A", CallCadence(days))


def activity(c, when):
    return CustomerActivity(c.tenant_id, c.id, ActivityType.CALL, "Call", when)


def follow_up(c, due):
    return CustomerFollowUp(c.tenant_id, c.id, uuid4(), due, "Follow up")


def test_build_includes_cadence_item():
    c, cc = customer()
    items = CallPlanningService.build([c], {cc.id: cc}, [], [], reference_at=REFERENCE)
    assert len(items) == 1
    assert items[0].item_type is CallPlanItemType.CADENCE
    assert items[0].due_at == REFERENCE.replace(day=12)


def test_build_anchors_cadence_to_latest_activity():
    c, cc = customer(14)
    items = CallPlanningService.build(
        [c], {cc.id: cc}, [activity(c, datetime(2026, 9, 1, 9, tzinfo=timezone.utc))], [], reference_at=REFERENCE
    )
    assert items[0].due_at == datetime(2026, 9, 15, 9, tzinfo=timezone.utc)


def test_build_includes_follow_up_items():
    c, cc = customer()
    due = datetime(2026, 9, 6, 9, tzinfo=timezone.utc)
    items = CallPlanningService.build([c], {cc.id: cc}, [], [follow_up(c, due)], reference_at=REFERENCE)
    assert any(item.item_type is CallPlanItemType.FOLLOW_UP and item.due_at == due for item in items)


def test_build_ignores_follow_ups_for_other_customers():
    c, cc = customer()
    other, _ = customer()
    items = CallPlanningService.build([c], {cc.id: cc}, [], [follow_up(other, REFERENCE)], reference_at=REFERENCE)
    assert all(item.customer_id == c.id for item in items)


def test_build_ignores_customer_without_configured_call_class():
    c, _ = customer()
    items = CallPlanningService.build([c], {}, [], [], reference_at=REFERENCE)
    assert items == ()


def test_build_omits_unconfigured_cadence():
    c = Customer(uuid4(), "Acme", uuid4(), uuid4())
    cc = CustomerCallClass(c.call_class_id, "E", "E", CallCadence(None))
    assert CallPlanningService.build([c], {cc.id: cc}, [], [], reference_at=REFERENCE) == ()


def test_build_orders_items_by_due_date():
    c, cc = customer()
    later = follow_up(c, datetime(2026, 9, 20, tzinfo=timezone.utc))
    earlier = follow_up(c, datetime(2026, 9, 6, tzinfo=timezone.utc))
    items = CallPlanningService.build([c], {cc.id: cc}, [], [later, earlier], reference_at=REFERENCE)
    assert [item.due_at for item in items] == sorted(item.due_at for item in items)


def test_for_customer_filters_queue():
    c, cc = customer()
    other, other_cc = customer()
    items = CallPlanningService.build(
        [c, other], {cc.id: cc, other_cc.id: other_cc}, [], [], reference_at=REFERENCE
    )
    result = CallPlanningService.for_customer(c.id, items)
    assert result
    assert all(item.customer_id == c.id for item in result)


def test_build_is_deterministic_for_same_due_time():
    c, cc = customer()
    first = follow_up(c, REFERENCE)
    second = follow_up(c, REFERENCE)
    result_one = CallPlanningService.build([c], {cc.id: cc}, [], [first, second], reference_at=REFERENCE)
    result_two = CallPlanningService.build([c], {cc.id: cc}, [], [second, first], reference_at=REFERENCE)
    assert result_one == result_two
