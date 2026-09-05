"""Customer 360 purchase-history presentation for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.customer_360 import Customer360PurchaseService
from phoenix_crm.services.purchase_history_boundary import PurchaseHistoryBoundary
from phoenix_crm.services.purchase_history_service import PurchaseHistoryProvider


@dataclass(frozen=True, slots=True)
class Customer360PurchaseSection:
    """Read-only purchase section suitable for Customer 360 presentation."""

    tenant_id: UUID
    customer_id: UUID
    available: bool
    purchase_count: int
    total_quantity: Decimal
    last_purchase_reference: str | None
    last_purchase_at: object | None
    recent_purchases: tuple[object, ...]
    purchased_solutions: tuple[str, ...]
    source_system: str


class Customer360PurchaseSectionService:
    """Compose the Customer 360 purchase section through the Phase 8 boundary."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        provider: PurchaseHistoryProvider | None = None,
        boundary: PurchaseHistoryBoundary | None = None,
        request_context: RequestContext | None = None,
        recent_limit: int = 5,
    ) -> Customer360PurchaseSection:
        if boundary is None:
            boundary = PurchaseHistoryBoundary(provider)
        view = Customer360PurchaseService.purchase_view(
            tenant_id=tenant_id,
            customer_id=customer_id,
            boundary=boundary,
            request_context=request_context,
            recent_limit=recent_limit,
        )
        summary = view.summary
        return Customer360PurchaseSection(
            tenant_id=tenant_id,
            customer_id=customer_id,
            available=view.available,
            purchase_count=summary.record_count,
            total_quantity=summary.total_quantity,
            last_purchase_reference=(
                summary.last_purchase.transaction_reference
                if summary.last_purchase is not None
                else None
            ),
            last_purchase_at=(
                summary.last_purchase.transaction_at
                if summary.last_purchase is not None
                else None
            ),
            recent_purchases=tuple(summary.recent_records),
            purchased_solutions=summary.solution_names,
            source_system=summary.source_system,
        )
