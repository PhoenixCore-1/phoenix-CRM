"""Tests for Phase 6.1 lead domain."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import Lead, LeadSource, LeadStatus


def make_lead() -> Lead:
    return Lead(
        tenant_id=uuid4(),
        name="  New Customer Lead  ",
        source=LeadSource.PROJECT_SITE_DISCOVERY,
        assigned_to_user_id=uuid4(),
        company_name="  Example Engineering  ",
        email="  contact@example.com  ",
        phone="  011 555 1234  ",
        mobile="  082 555 1234  ",
        notes="  Discovered during site visit.  ",
        access_scope_id=uuid4(),
    )


def test_lead_defaults_to_new_and_stores_core_scope_reference():
    lead = make_lead()
    assert lead.status is LeadStatus.NEW
    assert lead.source is LeadSource.PROJECT_SITE_DISCOVERY
    assert lead.assigned_to_user_id is not None
    assert lead.access_scope_id is not None


def test_lead_requires_name():
    with pytest.raises(ValueError, match="Lead name cannot be empty"):
        Lead(tenant_id=uuid4(), name="   ", source=LeadSource.MANUAL_ENTRY)


def test_lead_strips_fields_and_preserves_meaningful_optional_values():
    lead = make_lead()
    assert lead.name == "New Customer Lead"
    assert lead.company_name == "Example Engineering"
    assert lead.email == "contact@example.com"
    assert lead.phone == "011 555 1234"
    assert lead.mobile == "082 555 1234"
    assert lead.notes == "Discovered during site visit."


def test_blank_optional_fields_become_none():
    lead = Lead(
        tenant_id=uuid4(),
        name="Lead",
        source=LeadSource.WEBSITE,
        company_name="   ",
        email="   ",
        phone="   ",
        mobile="   ",
        notes="   ",
    )
    assert lead.company_name is None
    assert lead.email is None
    assert lead.phone is None
    assert lead.mobile is None
    assert lead.notes is None


def test_rename_updates_name_and_timestamp():
    lead = make_lead()
    before = lead.updated_at
    lead.rename("  Renamed Lead  ")
    assert lead.name == "Renamed Lead"
    assert lead.updated_at >= before


def test_rename_requires_name():
    lead = make_lead()
    with pytest.raises(ValueError, match="Lead name cannot be empty"):
        lead.rename("   ")


def test_update_notes_strips_value_and_updates_timestamp():
    lead = make_lead()
    before = lead.updated_at
    lead.update_notes("  Updated notes  ")
    assert lead.notes == "Updated notes"
    assert lead.updated_at >= before
    lead.update_notes("   ")
    assert lead.notes is None


def test_lead_supports_all_configured_sources():
    for source in LeadSource:
        lead = Lead(tenant_id=uuid4(), name="Lead", source=source)
        assert lead.source is source


def test_lead_timestamps_are_timezone_aware():
    lead = make_lead()
    assert lead.created_at.tzinfo is not None
    assert lead.updated_at.tzinfo is not None
    assert lead.created_at.utcoffset() is not None
    assert lead.updated_at.utcoffset() is not None
