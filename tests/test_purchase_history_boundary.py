from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.domain import PurchaseHistoryContract, PurchaseHistoryRecord
from phoenix_crm.services import PurchaseHistoryBoundary


class Provider:
    def __init__(self, contract):
        self.contract = contract

    def get_purchase_history(self, *, tenant_id, customer_id):
        return self.contract


def test_boundary_returns_provider_contract():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=customer_id,
        source_system="sales-source",
        records=(
            PurchaseHistoryRecord(
                tenant_id=tenant_id,
                customer_id=customer_id,
                transaction_reference="SO-1",
                transaction_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                solution_name="Anchor",
                quantity=1,
                source_system="sales-source",
            ),
        ),
    )
    assert PurchaseHistoryBoundary(Provider(contract)).get_for_customer(
        tenant_id=tenant_id, customer_id=customer_id
    ) == contract


def test_boundary_degrades_when_provider_unavailable():
    tenant_id, customer_id = uuid4(), uuid4()
    result = PurchaseHistoryBoundary().get_for_customer(tenant_id=tenant_id, customer_id=customer_id)
    assert result.records == ()
    assert result.source_system == "unavailable"


def test_boundary_degrades_when_provider_returns_none():
    tenant_id, customer_id = uuid4(), uuid4()
    result = PurchaseHistoryBoundary(Provider(None)).get_for_customer(
        tenant_id=tenant_id, customer_id=customer_id
    )
    assert result.records == ()
    assert result.source_system == "unavailable"


def test_boundary_rejects_mismatched_contract():
    tenant_id, customer_id = uuid4(), uuid4()
    contract = PurchaseHistoryContract(
        tenant_id=tenant_id,
        customer_id=uuid4(),
        source_system="sales-source",
    )
    with pytest.raises(ValueError):
        PurchaseHistoryBoundary(Provider(contract)).get_for_customer(
            tenant_id=tenant_id, customer_id=customer_id
        )


def test_boundary_enforces_core_access_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    context = RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset()),
    )
    with pytest.raises(PermissionError):
        PurchaseHistoryBoundary().get_for_customer(
            tenant_id=tenant_id, customer_id=customer_id, request_context=context
        )
