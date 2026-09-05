from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import PurchaseHistoryRecord
from phoenix_crm.services import PurchaseSummaryService


def record(tenant_id, customer_id, name, when, quantity):
    return PurchaseHistoryRecord(
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_reference=f"REF-{uuid4()}",
        transaction_at=datetime(2026, 1, when, tzinfo=timezone.utc),
        solution_name=name,
        quantity=Decimal(quantity),
        source_system="test-source",
    )


def test_summarize_returns_last_purchase_and_recent_records():
    tenant_id, customer_id = uuid4(), uuid4()
    records = [record(tenant_id, customer_id, "Anchor", 10, "2"), record(tenant_id, customer_id, "Screw", 20, "5")]
    summary = PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=records)
    assert summary.record_count == 2
    assert summary.total_quantity == Decimal("7")
    assert summary.last_purchase == records[1]
    assert summary.recent_records == (records[1], records[0])
    assert summary.solution_names == ("Screw", "Anchor")


def test_summarize_applies_recent_limit():
    tenant_id, customer_id = uuid4(), uuid4()
    records = [record(tenant_id, customer_id, f"S{i}", i + 1, "1") for i in range(5)]
    summary = PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=records, recent_limit=2)
    assert len(summary.recent_records) == 2


def test_summarize_excludes_other_tenant_and_customer_records():
    tenant_id, customer_id = uuid4(), uuid4()
    records = [
        record(tenant_id, customer_id, "Valid", 10, "2"),
        record(uuid4(), customer_id, "Other tenant", 20, "9"),
        record(tenant_id, uuid4(), "Other customer", 30, "9"),
    ]
    summary = PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=records)
    assert summary.record_count == 1
    assert summary.total_quantity == Decimal("2")


def test_summarize_requires_positive_recent_limit():
    with pytest.raises(ValueError):
        PurchaseSummaryService.summarize(tenant_id=uuid4(), customer_id=uuid4(), records=[], recent_limit=0)


def test_summarize_enforces_core_access_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    context = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset()),
    )
    with pytest.raises(PermissionError):
        PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=[], request_context=context)


def test_empty_history_is_supported():
    tenant_id, customer_id = uuid4(), uuid4()
    summary = PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=[])
    assert summary.record_count == 0
    assert summary.total_quantity == Decimal("0")
    assert summary.last_purchase is None
    assert summary.recent_records == ()
    assert summary.solution_names == ()
    assert summary.source_system == ""
