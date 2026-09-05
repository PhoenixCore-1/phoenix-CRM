"""Customer 360 document presentation boundary for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.services.customer_360_contract import Customer360Reference


@dataclass(frozen=True, slots=True)
class Customer360DocumentsSection:
    """Read-only Documents section for Customer 360."""

    tenant_id: UUID
    customer_id: UUID
    available: bool
    documents: tuple[Customer360Reference, ...]


class CustomerDocumentProvider(Protocol):
    """Published capability for resolving customer document references."""

    def references_for_customer(
        self, *, tenant_id: UUID, customer_id: UUID
    ) -> tuple[Customer360Reference, ...]:
        ...


class Customer360DocumentsService:
    """Compose document references without owning document storage."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        document_references: tuple[Customer360Reference, ...] = (),
        provider: CustomerDocumentProvider | None = None,
        request_context: RequestContext | None = None,
    ) -> Customer360DocumentsSection:
        Customer360DocumentsService._require_access(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=request_context,
        )
        available = provider is not None or bool(document_references)
        if provider is not None:
            document_references = provider.references_for_customer(
                tenant_id=tenant_id, customer_id=customer_id
            )

        documents = tuple(
            sorted(
                (
                    item
                    for item in document_references
                    if item.resource_type in {"document", "customer_document"}
                ),
                key=lambda item: ((item.label or "").lower(), str(item.resource_id)),
            )
        )
        return Customer360DocumentsSection(
            tenant_id=tenant_id,
            customer_id=customer_id,
            available=available,
            documents=documents,
        )

    @staticmethod
    def _require_access(
        *, tenant_id: UUID, customer_id: UUID, request_context: RequestContext | None
    ) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
