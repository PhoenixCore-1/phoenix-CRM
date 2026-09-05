"""Tests for Phase 5.6 call-plan timing."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.services import (
    CallPlanItem,
    CallPlanItemType,
    CallPlanTiming,
    CallPlanTimingService,
)

REFERENCE = datetime(2026, 9, 5, 10, tzinfo=timezone.utc)


def item(due_at):
    return CallPlanItem(uuid4(), "Acme", CallPlanItemType.FOLLOW_UP, due_at)


def test_past_item_is_overdue():
    assert CallPlanTimingService.classify(item(REFERENCE - timedelta(minutes=1)), reference_at=REFERENCE) is CallPlanTiming.OVERDUE


def test_exact_item_is_due():
    assert CallPlanTimingService.classify(item(REFERENCE), reference_at=REFERENCE) is CallPlanTiming.DUE


def test_future_item_is_upcoming():
    assert CallPlanTimingService.classify(item(REFERENCE + timedelta(minutes=1)), reference_at=REFERENCE) is CallPlanTiming.UPCOMING


def test_due_window_includes_item_after_reference():
    assert CallPlanTimingService.classify(item(REFERENCE + timedelta(minutes=30)), reference_at=REFERENCE, due_window_minutes=30) is CallPlanTiming.DUE


def test_item_after_due_window_is_upcoming():
    assert CallPlanTimingService.classify(item(REFERENCE + timedelta(minutes=31)), reference_at=REFERENCE, due_window_minutes=30) is CallPlanTiming.UPCOMING


def test_negative_due_window_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        CallPlanTimingService.classify(item(REFERENCE), reference_at=REFERENCE, due_window_minutes=-1)


def test_classify_queue_preserves_order():
    items = (item(REFERENCE - timedelta(days=1)), item(REFERENCE), item(REFERENCE + timedelta(days=1)))
    result = CallPlanTimingService.classify_queue(items, reference_at=REFERENCE)
    assert [entry.item for entry in result] == list(items)
    assert [entry.timing for entry in result] == [CallPlanTiming.OVERDUE, CallPlanTiming.DUE, CallPlanTiming.UPCOMING]


def test_filter_by_timing_preserves_queue_order():
    items = (item(REFERENCE - timedelta(days=1)), item(REFERENCE), item(REFERENCE + timedelta(days=1)))
    classified = CallPlanTimingService.classify_queue(items, reference_at=REFERENCE)
    due = CallPlanTimingService.filter_by_timing(classified, CallPlanTiming.DUE)
    assert len(due) == 1
    assert due[0].item is items[1]
