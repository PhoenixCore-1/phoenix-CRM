"""Customer 360 purchase-history consumption for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import PurchaseHistoryRecord
from phoenix_crm.services.purchase_history_boundary import PurchaseHistoryBoundary
from phoenix_crm.services.purchase_summary import PurchaseHistorySummary, PurchaseSummaryService


@dataclass(frozen=True, slots=True)
class Customer360PurchaseView:
    """Purchase-history presentation data for the Customer 360 view."""

    tenant_id: UUID
    customer_id: UUID
    summary: PurchaseHistorySummary
    available: bool


class Customer360PurchaseService:
    """Compose purchase information for Customer 360 without owning transactions."""

    @staticmethod
    def purchase_view(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        boundary: PurchaseHistoryBoundary,
        request_context: RequestContext | None = None,
        recent_limit: int = 5,
    ) -> Customer360PurchaseView:
        contract = boundary.get_for_customer(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )
        records: tuple[PurchaseHistoryRecord, ...] = contract.records
        summary = PurchaseSummaryService.summarize(
            tenant_id=tenant_id,
            customer_id=customer_id,
            records=records,
            request_context=request_context,
            recent_limit=recent_limit,
        )
        return Customer360PurchaseView(
            tenant_id=tenant_id,
            customer_id=customer_id,
            summary=summary,
            available=contract.source_system != PurchaseHistoryBoundary.SOURCE_UNAVAILABLE,
        )
