from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.domain import PurchaseHistoryContract, PurchaseHistoryRecord
from phoenix_crm.services import Customer360PurchaseSectionService, PurchaseHistoryBoundary


class Provider:
    def __init__(self, contract):
        self.contract = contract

    def get_purchase_history(self, *, tenant_id, customer_id):
        return self.contract


def record(tenant_id, customer_id, reference, day, solution="Anchor"):
    return PurchaseHistoryRecord(
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_reference=reference,
        transaction_at=datetime(2026, 1, day, tzinfo=timezone.utc),
        solution_name=solution,
        quantity=Decimal("2"),
        source_system="sales",
    )


def test_purchase_section_composes_summary():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        records=(record(tenant_id, customer_id, "A", 1), record(tenant_id, customer_id, "B", 2, "Chemical")),
        source_system="sales",
    )
    section = Customer360PurchaseSectionService.build(
        tenant_id=tenant_id, customer_id=customer_id, provider=Provider(contract)
    )
    assert section.available is True
    assert section.purchase_count == 2
    assert section.total_quantity == Decimal("4")
    assert section.last_purchase_reference == "B"
    assert section.purchased_solutions == ("Chemical", "Anchor")


def test_purchase_section_gracefully_degrades_without_provider():
    tenant_id, customer_id = uuid4(), uuid4()
    section = Customer360PurchaseSectionService.build(
        tenant_id=tenant_id, customer_id=customer_id
    )
    assert section.available is False
    assert section.purchase_count == 0
    assert section.total_quantity == Decimal("0")
    assert section.recent_purchases == ()


def test_purchase_section_honors_recent_limit():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        records=tuple(record(tenant_id, customer_id, str(day), day) for day in range(1, 4)),
        source_system="sales",
    )
    section = Customer360PurchaseSectionService.build(
        tenant_id=tenant_id, customer_id=customer_id, provider=Provider(contract), recent_limit=2
    )
    assert len(section.recent_purchases) == 2
    assert section.recent_purchases[0].transaction_reference == "3"


def test_purchase_section_enforces_provider_contract_customer_boundary():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        records=(),
        source_system="sales",
    )
    with pytest.raises(ValueError):
        Customer360PurchaseSectionService.build(
            tenant_id=tenant_id, customer_id=customer_id, provider=Provider(contract)
        )


def test_purchase_section_rejects_invalid_recent_limit():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(ValueError):
        Customer360PurchaseSectionService.build(
            tenant_id=tenant_id, customer_id=customer_id, recent_limit=0
        )


def test_purchase_section_preserves_source_system():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        records=(record(tenant_id, customer_id, "A", 1),),
        source_system="erp",
    )
    section = Customer360PurchaseSectionService.build(
        tenant_id=tenant_id, customer_id=customer_id, provider=Provider(contract)
    )
    assert section.source_system == "erp"
