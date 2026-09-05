"""Purchase history contract objects for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class PurchaseRecordStatus(str, Enum):
    """Business status supplied by the authoritative purchase source."""

    COMPLETED = "completed"
    OPEN = "open"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PurchaseHistoryRecord:
    """Read-only CRM representation of one purchase-history record.

    CRM presents this information but does not become the source of truth for
    orders, invoices, accounting, inventory valuation, or financial posting.
    The source system owns the authoritative transaction and reference.
    """

    tenant_id: UUID
    customer_id: UUID
    transaction_reference: str
    transaction_at: datetime
    solution_name: str
    quantity: Decimal
    source_system: str
    id: UUID = field(default_factory=uuid4)
    currency: str | None = None
    total_value: Decimal | None = None
    status: PurchaseRecordStatus = PurchaseRecordStatus.UNKNOWN
    source_reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.transaction_reference.strip():
            raise ValueError("transaction_reference cannot be empty")
        if not self.solution_name.strip():
            raise ValueError("solution_name cannot be empty")
        if not self.source_system.strip():
            raise ValueError("source_system cannot be empty")
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if self.total_value is not None and self.total_value < 0:
            raise ValueError("total_value cannot be negative")
        self._validate_currency()

    def _validate_currency(self) -> None:
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be empty when supplied")


@dataclass(frozen=True, slots=True)
class PurchaseHistoryContract:
    """Provider-independent contract for CRM purchase-history consumption."""

    tenant_id: UUID
    customer_id: UUID
    records: tuple[PurchaseHistoryRecord, ...] = ()
    source_system: str = ""
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.source_system.strip():
            raise ValueError("source_system cannot be empty")
        for record in self.records:
            if record.tenant_id != self.tenant_id:
                raise ValueError("purchase record tenant does not match contract tenant")
            if record.customer_id != self.customer_id:
                raise ValueError("purchase record customer does not match contract customer")
            if record.source_system != self.source_system:
                raise ValueError("purchase record source does not match contract source")
