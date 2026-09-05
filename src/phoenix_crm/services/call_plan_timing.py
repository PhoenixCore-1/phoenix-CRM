"""Temporal classification for Phoenix CRM 360 call-planning items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from phoenix_crm.services.call_planning import CallPlanItem


class CallPlanTiming(str, Enum):
    """Temporal state of a call-planning item."""

    OVERDUE = "overdue"
    DUE = "due"
    UPCOMING = "upcoming"


@dataclass(frozen=True, slots=True)
class TimedCallPlanItem:
    """Call-plan item with resolved temporal state."""

    item: CallPlanItem
    timing: CallPlanTiming


class CallPlanTimingService:
    """Classify planning items relative to an explicit reference time."""

    @staticmethod
    def classify(
        item: CallPlanItem,
        *,
        reference_at: datetime,
        due_window_minutes: int = 0,
    ) -> CallPlanTiming:
        """Classify an item as overdue, due, or upcoming.

        ``due_window_minutes`` defines the inclusive window after the reference
        time that is treated as due. A zero-minute window means only an exact
        due timestamp is due; earlier timestamps are overdue.
        """
        if due_window_minutes < 0:
            raise ValueError("due_window_minutes must be non-negative")
        due_until = reference_at + timedelta(minutes=due_window_minutes)
        if item.due_at < reference_at:
            return CallPlanTiming.OVERDUE
        if item.due_at <= due_until:
            return CallPlanTiming.DUE
        return CallPlanTiming.UPCOMING

    @staticmethod
    def classify_queue(
        items: tuple[CallPlanItem, ...],
        *,
        reference_at: datetime,
        due_window_minutes: int = 0,
    ) -> tuple[TimedCallPlanItem, ...]:
        """Classify a complete queue while preserving its deterministic order."""
        return tuple(
            TimedCallPlanItem(
                item=item,
                timing=CallPlanTimingService.classify(
                    item,
                    reference_at=reference_at,
                    due_window_minutes=due_window_minutes,
                ),
            )
            for item in items
        )

    @staticmethod
    def filter_by_timing(
        items: tuple[TimedCallPlanItem, ...],
        timing: CallPlanTiming,
    ) -> tuple[TimedCallPlanItem, ...]:
        """Return items in one temporal state, preserving queue order."""
        return tuple(item for item in items if item.timing is timing)
