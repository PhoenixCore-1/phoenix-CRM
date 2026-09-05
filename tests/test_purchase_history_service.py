from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import PurchaseHistoryContract, PurchaseHistoryRecord
from phoenix_crm.services.purchase_history_service import PurchaseHistoryService


class StubPurchaseProvider:
    def __init__(self, contract=None):
        self.contract = contract
        self.calls = []

    def get_purchase_history(self, *, tenant_id, customer_id):
        self.calls.append((tenant_id, customer_id))
        return self.contract


def make_record(tenant_id, customer_id, reference, when):
    return PurchaseHistoryRecord(
        tenant_id=tenant_id,
        customer_id=customer_id,
        transaction_reference=reference,
        transaction_at=when,
        solution_name="Anchor solution",
        quantity=Decimal("2"),
        source_system="sales",
    )


def make_context(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_returns_records_newest_first():
    tenant_id, customer_id = uuid4(), uuid4()
    older = make_record(tenant_id, customer_id, "OLD", datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = make_record(tenant_id, customer_id, "NEW", datetime(2026, 2, 1, tzinfo=timezone.utc))
    provider = StubPurchaseProvider(
        PurchaseHistoryContract(tenant_id, customer_id, (older, newer), "sales")
    )

    result = PurchaseHistoryService.for_customer(
        tenant_id=tenant_id, customer_id=customer_id, provider=provider
    )

    assert [item.transaction_reference for item in result] == ["NEW", "OLD"]


def test_unavailable_provider_degrades_to_empty_result():
    tenant_id, customer_id = uuid4(), uuid4()
    provider = StubPurchaseProvider()

    assert PurchaseHistoryService.for_customer(
        tenant_id=tenant_id, customer_id=customer_id, provider=provider
    ) == ()


def test_tenant_scope_is_enforced_before_provider_call():
    tenant_id, customer_id = uuid4(), uuid4()
    provider = StubPurchaseProvider()
    context = make_context(uuid4(), customer_id)

    with pytest.raises(PermissionError):
        PurchaseHistoryService.for_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            provider=provider,
            request_context=context,
        )
    assert provider.calls == []


def test_customer_access_scope_is_enforced_before_provider_call():
    tenant_id, customer_id = uuid4(), uuid4()
    provider = StubPurchaseProvider()
    context = make_context(tenant_id, uuid4())

    with pytest.raises(PermissionError):
        PurchaseHistoryService.for_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            provider=provider,
            request_context=context,
        )
    assert provider.calls == []


def test_provider_contract_mismatch_is_rejected():
    tenant_id, customer_id = uuid4(), uuid4()
    wrong_customer = uuid4()
    record = make_record(tenant_id, wrong_customer, "WRONG", datetime.now(timezone.utc))
    provider = StubPurchaseProvider(
        PurchaseHistoryContract(tenant_id, wrong_customer, (record,), "sales")
    )

    with pytest.raises(ValueError):
        PurchaseHistoryService.for_customer(
            tenant_id=tenant_id, customer_id=customer_id, provider=provider
        )


def test_access_scope_allows_authorized_customer():
    tenant_id, customer_id = uuid4(), uuid4()
    record = make_record(tenant_id, customer_id, "OK", datetime.now(timezone.utc))
    provider = StubPurchaseProvider(
        PurchaseHistoryContract(tenant_id, customer_id, (record,), "sales")
    )

    result = PurchaseHistoryService.for_customer(
        tenant_id=tenant_id,
        customer_id=customer_id,
        provider=provider,
        request_context=make_context(tenant_id, customer_id),
    )

    assert [item.transaction_reference for item in result] == ["OK"]
