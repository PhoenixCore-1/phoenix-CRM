from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import PurchaseHistoryContract, PurchaseHistoryRecord
from phoenix_crm.services import Customer360PurchaseService, PurchaseHistoryBoundary


class Provider:
    def __init__(self, contract):
        self.contract = contract

    def get_purchase_history(self, *, tenant_id, customer_id):
        return self.contract


def make_contract(tenant_id, customer_id):
    return PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        source_system="authoritative-source",
        records=(
            PurchaseHistoryRecord(
                tenant_id=tenant_id,
                customer_id=customer_id,
                transaction_reference="TX-1",
                transaction_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
                solution_name="Anchor",
                quantity=Decimal("4"),
                source_system="authoritative-source",
            ),
        ),
    )


def test_customer_360_consumes_purchase_history_through_boundary():
    tenant_id, customer_id = uuid4(), uuid4()
    view = Customer360PurchaseService.purchase_view(
        tenant_id=tenant_id,
        customer_id=customer_id,
        boundary=PurchaseHistoryBoundary(Provider(make_contract(tenant_id, customer_id))),
    )
    assert view.available is True
    assert view.summary.customer_id == customer_id
    assert view.summary.record_count == 1
    assert view.summary.total_quantity == Decimal("4")


def test_customer_360_gracefully_handles_unavailable_purchase_history():
    tenant_id, customer_id = uuid4(), uuid4()
    view = Customer360PurchaseService.purchase_view(
        tenant_id=tenant_id,
        customer_id=customer_id,
        boundary=PurchaseHistoryBoundary(),
    )
    assert view.available is False
    assert view.summary.record_count == 0
    assert view.summary.last_purchase is None


def test_customer_360_preserves_core_access_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    context = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset()),
    )
    with pytest.raises(PermissionError):
        Customer360PurchaseService.purchase_view(
            tenant_id=tenant_id,
            customer_id=customer_id,
            boundary=PurchaseHistoryBoundary(),
            request_context=context,
        )
