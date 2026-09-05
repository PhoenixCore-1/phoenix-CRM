"""Runtime publisher for CRM's versioned cross-module capabilities."""

from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from phoenix_crm.api.published import (
    CRM_CUSTOMER_CONTRACT,
    CRM_CUSTOMER_CONTEXT_CAPABILITY,
    CustomerContext,
    CustomerReference,
)


class CRMCustomerCapabilityProvider(Protocol):
    """CRM-owned provider used by the published runtime boundary."""

    def get_customer(self, *, tenant_id: str, customer_id: str) -> CustomerReference | None:
        ...

    def get_customer_context(self, *, tenant_id: str, customer_id: str) -> CustomerContext | None:
        ...


class CRMPublishedCapabilityHandler:
    """Expose CRM read capabilities without exposing CRM implementation types."""

    def __init__(self, provider: CRMCustomerCapabilityProvider) -> None:
        self._provider = provider

    def __call__(self, *, operation: str, context: object, payload: dict | None = None):
        """Handle Core-routed CRM capability calls using Core-supplied context."""
        tenant_id = self._tenant_id(context)
        values = payload or {}
        customer_id = str(values.get("customer_id", "")).strip()
        if not customer_id:
            raise ValueError("customer_id is required")

        if operation == "get_customer":
            result = self._provider.get_customer(
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
            return asdict(result) if result is not None else None

        if operation == "get_customer_context":
            result = self._provider.get_customer_context(
                tenant_id=tenant_id,
                customer_id=customer_id,
            )
            return asdict(result) if result is not None else None

        raise ValueError(f"Unsupported CRM operation: {operation}")

    @staticmethod
    def _tenant_id(context: object) -> str:
        tenant = getattr(context, "tenant_id", None)
        if tenant is None:
            organisation_id = getattr(context, "organisation_id", None)
            tenant = organisation_id
        value = str(tenant or "").strip()
        if not value:
            raise PermissionError("CRM capability requires a Core tenant context")
        return value


__all__ = [
    "CRM_CUSTOMER_CONTRACT",
    "CRM_CUSTOMER_CONTEXT_CAPABILITY",
    "CRMCustomerCapabilityProvider",
    "CRMPublishedCapabilityHandler",
]
