"""Purchase history summary service for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import PurchaseHistoryRecord


@dataclass(frozen=True, slots=True)
class PurchaseHistorySummary:
    """Relationship-oriented summary of authoritative purchase history."""

    tenant_id: UUID
    customer_id: UUID
    record_count: int
    total_quantity: Decimal
    last_purchase: PurchaseHistoryRecord | None
    recent_records: tuple[PurchaseHistoryRecord, ...]
    solution_names: tuple[str, ...]
    source_system: str


class PurchaseSummaryService:
    """Build deterministic, read-only purchase summaries for CRM."""

    @staticmethod
    def summarize(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        records: list[PurchaseHistoryRecord] | tuple[PurchaseHistoryRecord, ...],
        request_context: RequestContext | None = None,
        recent_limit: int = 5,
    ) -> PurchaseHistorySummary:
        if recent_limit <= 0:
            raise ValueError("recent_limit must be positive")
        PurchaseSummaryService._require_customer_scope(customer_id, tenant_id, request_context)
        items = [
            record for record in records
            if record.tenant_id == tenant_id and record.customer_id == customer_id
        ]
        items.sort(key=lambda record: (record.transaction_at, str(record.id)), reverse=True)
        source_system = items[0].source_system if items else ""
        solution_names = tuple(dict.fromkeys(record.solution_name for record in items))
        return PurchaseHistorySummary(
            tenant_id=tenant_id,
            customer_id=customer_id,
            record_count=len(items),
            total_quantity=sum((record.quantity for record in items), Decimal("0")),
            last_purchase=items[0] if items else None,
            recent_records=tuple(items[:recent_limit]),
            solution_names=solution_names,
            source_system=source_system,
        )

    @staticmethod
    def _require_customer_scope(
        customer_id: UUID,
        tenant_id: UUID,
        request_context: RequestContext | None,
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
