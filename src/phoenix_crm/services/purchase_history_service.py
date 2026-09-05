"""Purchase history application service for Phoenix CRM 360."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import PurchaseHistoryContract, PurchaseHistoryRecord


class PurchaseHistoryProvider(Protocol):
    """Provider capability for an authoritative purchase-history source."""

    def get_purchase_history(
        self, *, tenant_id: UUID, customer_id: UUID
    ) -> PurchaseHistoryContract | None:
        """Return authoritative purchase history, or None when unavailable."""


class PurchaseHistoryService:
    """Retrieve purchase history without owning the authoritative transactions."""

    @staticmethod
    def for_customer(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        provider: PurchaseHistoryProvider,
        request_context: RequestContext | None = None,
    ) -> tuple[PurchaseHistoryRecord, ...]:
        """Return purchase records visible to the caller for one customer.

        An unavailable provider degrades to an empty result. The service never
        mutates the provider or creates a second transactional source of truth.
        """
        PurchaseHistoryService._require_customer_scope(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )
        contract = provider.get_purchase_history(
            tenant_id=tenant_id,
            customer_id=customer_id,
        )
        if contract is None:
            return ()
        if contract.tenant_id != tenant_id or contract.customer_id != customer_id:
            raise ValueError("purchase history contract does not match requested customer")
        return tuple(
            sorted(
                contract.records,
                key=lambda record: (record.transaction_at, str(record.id)),
                reverse=True,
            )
        )

    @staticmethod
    def _require_customer_scope(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
