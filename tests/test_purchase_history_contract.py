from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.domain import (
    PurchaseHistoryContract,
    PurchaseHistoryRecord,
    PurchaseRecordStatus,
)


def make_record(*, tenant_id, customer_id, source_system="sales"):
    return PurchaseHistoryRecord(
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_reference="SO-1001",
        transaction_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        solution_name="Anchor System",
        quantity=Decimal("10"),
        source_system=source_system,
        currency="ZAR",
        total_value=Decimal("1250.00"),
        status=PurchaseRecordStatus.COMPLETED,
        source_reference="source-1001",
    )


def test_purchase_record_accepts_contract_fields():
    tenant_id = uuid4()
    customer_id = uuid4()

    record = make_record(tenant_id=tenant_id, customer_id=customer_id)

    assert record.tenant_id == tenant_id
    assert record.customer_id == customer_id
    assert record.transaction_reference == "SO-1001"
    assert record.quantity == Decimal("10")
    assert record.total_value == Decimal("1250.00")
    assert record.currency == "ZAR"
    assert record.status is PurchaseRecordStatus.COMPLETED


def test_purchase_record_rejects_empty_required_fields():
    tenant_id = uuid4()
    customer_id = uuid4()

    with pytest.raises(ValueError, match="transaction_reference"):
        PurchaseHistoryRecord(
            tenant_id=tenant_id,
            customer_id=customer_id,
            transaction_reference=" ",
            transaction_at=datetime.now(timezone.utc),
            solution_name="Anchor",
            quantity=Decimal("1"),
            source_system="sales",
        )

    with pytest.raises(ValueError, match="solution_name"):
        PurchaseHistoryRecord(
            tenant_id=tenant_id,
            customer_id=customer_id,
            transaction_reference="SO-1",
            transaction_at=datetime.now(timezone.utc),
            solution_name=" ",
            quantity=Decimal("1"),
            source_system="sales",
        )

    with pytest.raises(ValueError, match="source_system"):
        PurchaseHistoryRecord(
            tenant_id=tenant_id,
            customer_id=customer_id,
            transaction_reference="SO-1",
            transaction_at=datetime.now(timezone.utc),
            solution_name="Anchor",
            quantity=Decimal("1"),
            source_system=" ",
        )


def test_purchase_record_rejects_negative_quantity_or_value():
    tenant_id = uuid4()
    customer_id = uuid4()

    with pytest.raises(ValueError, match="quantity"):
        PurchaseHistoryRecord(
            tenant_id=tenant_id,
            customer_id=customer_id,
            transaction_reference="SO-1",
            transaction_at=datetime.now(timezone.utc),
            solution_name="Anchor",
            quantity=Decimal("-1"),
            source_system="sales",
        )

    with pytest.raises(ValueError, match="total_value"):
        PurchaseHistoryRecord(
            tenant_id=tenant_id,
            customer_id=customer_id,
            transaction_reference="SO-1",
            transaction_at=datetime.now(timezone.utc),
            solution_name="Anchor",
            quantity=Decimal("1"),
            source_system="sales",
            total_value=Decimal("-1"),
        )


def test_contract_accepts_matching_records():
    tenant_id = uuid4()
    customer_id = uuid4()
    record = make_record(tenant_id=tenant_id, customer_id=customer_id)

    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        records=(record,),
        source_system="sales",
    )

    assert contract.records == (record,)


def test_contract_rejects_cross_tenant_record():
    tenant_id = uuid4()
    customer_id = uuid4()
    record = make_record(tenant_id=uuid4(), customer_id=customer_id)

    with pytest.raises(ValueError, match="tenant"):
        PurchaseHistoryContract(
            tenant_id=tenant_id,
            customer_id=customer_id,
            records=(record,),
            source_system="sales",
        )


def test_contract_rejects_cross_customer_record():
    tenant_id = uuid4()
    customer_id = uuid4()
    record = make_record(tenant_id=tenant_id, customer_id=uuid4())

    with pytest.raises(ValueError, match="customer"):
        PurchaseHistoryContract(
            tenant_id=tenant_id,
            customer_id=customer_id,
            records=(record,),
            source_system="sales",
        )


def test_contract_rejects_mismatched_source_system():
    tenant_id = uuid4()
    customer_id = uuid4()
    record = make_record(tenant_id=tenant_id, customer_id=customer_id, source_system="sage")

    with pytest.raises(ValueError, match="source"):
        PurchaseHistoryContract(
            tenant_id=tenant_id,
            customer_id=customer_id,
            records=(record,),
            source_system="sales",
        )
