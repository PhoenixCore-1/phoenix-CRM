from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import PurchaseHistoryRecord, PurchaseRecordStatus
from phoenix_crm.services import PurchaseSummaryService


def make_record(tenant_id, customer_id, reference, day, status=PurchaseRecordStatus.COMPLETED):
    return PurchaseHistoryRecord(
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_reference=reference,
        transaction_at=datetime(2026, 1, day, tzinfo=timezone.utc),
        solution_name="Anchor",
        quantity=Decimal("2"),
        source_system="source",
        status=status,
    )


def context_for(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_summary_does_not_mutate_input_records():
    tenant_id, customer_id = uuid4(), uuid4()
    records = [make_record(tenant_id, customer_id, "A", 1), make_record(tenant_id, customer_id, "B", 2)]
    original = tuple(records)
    PurchaseSummaryService.summarize(tenant_id=tenant_id, customer_id=customer_id, records=records)
    assert tuple(records) == original


def test_summary_requires_core_tenant_match():
    tenant_id, customer_id = uuid4(), uuid4()
    context = context_for(uuid4(), customer_id)
    with pytest.raises(PermissionError):
        PurchaseSummaryService.summarize(
            tenant_id=tenant_id, customer_id=customer_id, records=[], request_context=context
        )


def test_summary_allows_customer_in_core_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    summary = PurchaseSummaryService.summarize(
        tenant_id=tenant_id,
        customer_id=customer_id,
        records=[make_record(tenant_id, customer_id, "A", 1)],
        request_context=context_for(tenant_id, customer_id),
    )
    assert summary.record_count == 1


def test_summary_order_is_deterministic_for_equal_timestamps():
    tenant_id, customer_id = uuid4(), uuid4()
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = PurchaseHistoryRecord(
        tenant_id=tenant_id, customer_id=customer_id, transaction_reference="A",
        transaction_at=timestamp, solution_name="A", quantity=1, source_system="source",
    )
    second = PurchaseHistoryRecord(
        tenant_id=tenant_id, customer_id=customer_id, transaction_reference="B",
        transaction_at=timestamp, solution_name="B", quantity=1, source_system="source",
    )
    expected = tuple(sorted((first, second), key=lambda r: (r.transaction_at, str(r.id)), reverse=True))
    summary = PurchaseSummaryService.summarize(
        tenant_id=tenant_id, customer_id=customer_id, records=[first, second]
    )
    assert summary.recent_records == expected


def test_summary_does_not_treat_transaction_value_as_financial_total():
    tenant_id, customer_id = uuid4(), uuid4()
    record = PurchaseHistoryRecord(
        tenant_id=tenant_id, customer_id=customer_id, transaction_reference="A",
        transaction_at=datetime(2026, 1, 1, tzinfo=timezone.utc), solution_name="A",
        quantity=3, source_system="source", currency="ZAR", total_value=Decimal("9999"),
    )
    summary = PurchaseSummaryService.summarize(
        tenant_id=tenant_id, customer_id=customer_id, records=[record]
    )
    assert summary.total_quantity == Decimal("3")
    assert not hasattr(summary, "total_value")
