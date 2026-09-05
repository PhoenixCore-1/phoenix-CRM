"""Tests for Phase 6.6 lead activity integration."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import ActivityType, CustomerActivity, Lead, LeadSource
from phoenix_crm.services import LeadActivityService


def make_lead(tenant_id=None, **kwargs):
    return Lead(
        tenant_id=tenant_id or uuid4(),
        name=kwargs.pop("name", "Acme Lead"),
        source=LeadSource.MANUAL_ENTRY,
        **kwargs,
    )


def make_activity(lead, *, occurred_at=None, metadata=None):
    activity = CustomerActivity(
        tenant_id=lead.tenant_id,
        customer_id=uuid4(),
        activity_type=ActivityType.CALL,
        subject="Lead call",
        occurred_at=occurred_at or datetime.now(timezone.utc),
        metadata=metadata or {},
    )
    LeadActivityService.attach_lead_reference(activity, lead)
    return activity


def test_attach_lead_reference_is_tenant_safe():
    lead = make_lead()
    activity = CustomerActivity(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        activity_type=ActivityType.CALL,
        subject="Lead call",
        occurred_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError, match="same tenant"):
        LeadActivityService.attach_lead_reference(activity, lead)


def test_record_activity_requires_matching_lead_reference():
    lead = make_lead()
    activity = CustomerActivity(
        tenant_id=lead.tenant_id,
        customer_id=uuid4(),
        activity_type=ActivityType.CALL,
        subject="Lead call",
        occurred_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError, match="lead reference"):
        LeadActivityService.record_activity(activity, lead)


def test_record_activity_accepts_attached_lead_reference():
    lead = make_lead()
    activity = make_activity(lead)
    assert LeadActivityService.record_activity(activity, lead) is activity


def test_history_for_lead_returns_newest_first():
    lead = make_lead()
    older = make_activity(lead, occurred_at=datetime.now(timezone.utc) - timedelta(days=2))
    newer = make_activity(lead, occurred_at=datetime.now(timezone.utc) - timedelta(days=1))
    result = LeadActivityService.history_for_lead(lead, [older, newer])
    assert [entry.activity.id for entry in result] == [newer.id, older.id]


def test_history_for_lead_filters_by_time_window():
    lead = make_lead()
    older = make_activity(lead, occurred_at=datetime.now(timezone.utc) - timedelta(days=5))
    recent = make_activity(lead, occurred_at=datetime.now(timezone.utc) - timedelta(days=1))
    result = LeadActivityService.history_for_lead(
        lead,
        [older, recent],
        after=datetime.now(timezone.utc) - timedelta(days=2),
    )
    assert [entry.activity.id for entry in result] == [recent.id]


def test_history_for_lead_excludes_other_tenant_even_with_same_lead_reference():
    lead = make_lead()
    foreign = make_activity(lead)
    foreign.tenant_id = uuid4()
    result = LeadActivityService.history_for_lead(lead, [foreign])
    assert result == ()


def test_history_marks_converted_lead():
    lead = make_lead()
    activity = make_activity(lead)
    lead.start_qualification()
    lead.qualify()
    lead.mark_potential_customer()
    lead.convert()
    result = LeadActivityService.history_for_lead(lead, [activity])
    assert result[0].is_converted_lead is True


def test_existing_activity_metadata_is_preserved_when_attaching_lead():
    lead = make_lead()
    activity = make_activity(lead, metadata={"channel": "phone"})
    assert activity.metadata["channel"] == "phone"
    assert activity.metadata["lead_id"] == str(lead.id)
