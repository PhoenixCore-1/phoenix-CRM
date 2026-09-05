"""Relationship timeline services for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from phoenix_crm.domain import CustomerActivity


@dataclass(frozen=True, slots=True)
class ActivityTimelineEntry:
    """Presentation-ready context around one CRM relationship activity."""

    activity: CustomerActivity
    customer_id: UUID
    contact_id: UUID | None
    site_id: UUID | None
    site_party_id: UUID | None
    has_relationship_context: bool


class ActivityTimelineService:
    """Build a chronological relationship timeline without owning other modules."""

    @staticmethod
    def for_customer(
        customer_id: UUID,
        activities: list[CustomerActivity],
        *,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> tuple[ActivityTimelineEntry, ...]:
        """Return customer history as context-rich, newest-first timeline entries."""
        history = [activity for activity in activities if activity.customer_id == customer_id]
        if after is not None:
            history = [activity for activity in history if activity.occurred_at >= after]
        if before is not None:
            history = [activity for activity in history if activity.occurred_at <= before]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(ActivityTimelineService._entry(activity) for activity in history)

    @staticmethod
    def for_contact(
        contact_id: UUID,
        activities: list[CustomerActivity],
    ) -> tuple[ActivityTimelineEntry, ...]:
        """Return a contact's relationship timeline, newest first."""
        history = [activity for activity in activities if activity.contact_id == contact_id]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(ActivityTimelineService._entry(activity) for activity in history)

    @staticmethod
    def for_site(
        site_id: UUID,
        activities: list[CustomerActivity],
    ) -> tuple[ActivityTimelineEntry, ...]:
        """Return activities associated with a CRM customer site."""
        history = [activity for activity in activities if activity.site_id == site_id]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(ActivityTimelineService._entry(activity) for activity in history)

    @staticmethod
    def for_site_party(
        site_party_id: UUID,
        activities: list[CustomerActivity],
    ) -> tuple[ActivityTimelineEntry, ...]:
        """Return activities associated with a CRM project/site party relationship."""
        history = [activity for activity in activities if activity.site_party_id == site_party_id]
        history.sort(key=lambda activity: (activity.occurred_at, str(activity.id)), reverse=True)
        return tuple(ActivityTimelineService._entry(activity) for activity in history)

    @staticmethod
    def _entry(activity: CustomerActivity) -> ActivityTimelineEntry:
        return ActivityTimelineEntry(
            activity=activity,
            customer_id=activity.customer_id,
            contact_id=activity.contact_id,
            site_id=activity.site_id,
            site_party_id=activity.site_party_id,
            has_relationship_context=any(
                value is not None
                for value in (activity.contact_id, activity.site_id, activity.site_party_id)
            ),
        )
