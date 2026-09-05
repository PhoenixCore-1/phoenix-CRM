"""Optional purchase-history integration boundary for Phoenix CRM 360."""

from __future__ import annotations

from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import PurchaseHistoryContract
from phoenix_crm.services.purchase_history_service import PurchaseHistoryProvider


class PurchaseHistoryBoundary:
    """Resolve purchase history through an optional provider capability.

    CRM depends on this boundary rather than on Sales, Sage, ERP, or another
    module implementation. When the capability is unavailable, callers receive
    an empty contract rather than a module dependency failure.
    """

    SOURCE_UNAVAILABLE = "unavailable"

    def __init__(self, provider: PurchaseHistoryProvider | None = None) -> None:
        self._provider = provider

    def get_for_customer(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        request_context: RequestContext | None = None,
    ) -> PurchaseHistoryContract:
        if request_context is not None:
            if request_context.tenant.tenant_id != str(tenant_id):
                raise PermissionError("Core access scope does not include this customer")
            if not request_context.can_access_resource(str(customer_id)):
                raise PermissionError("Core access scope does not include this customer")

        if self._provider is None:
            return PurchaseHistoryContract(
                tenant_id=tenant_id,
                customer_id=customer_id,
                records=(),
                source_system=self.SOURCE_UNAVAILABLE,
            )

        contract = self._provider.get_purchase_history(
            tenant_id=tenant_id,
            customer_id=customer_id,
        )
        if contract is None:
            return PurchaseHistoryContract(
                tenant_id=tenant_id,
                customer_id=customer_id,
                records=(),
                source_system=self.SOURCE_UNAVAILABLE,
            )
        if contract.tenant_id != tenant_id or contract.customer_id != customer_id:
            raise ValueError("purchase history contract does not match requested customer")
        return contract
