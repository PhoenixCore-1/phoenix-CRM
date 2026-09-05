"""Published CRM contract models for cross-module consumption.

These are transport-neutral DTOs. Consumers must not import CRM domain,
persistence, or service implementations.
"""

from __future__ import annotations

from dataclasses import dataclass

CRM_CUSTOMER_CONTRACT = "crm.customer.v1"
CRM_CONTACT_CONTRACT = "crm.contact.v1"
CRM_CUSTOMER_CONTEXT_CAPABILITY = "crm.customer_context"


@dataclass(frozen=True)
class CustomerReference:
    """Stable customer identity exposed outside CRM."""

    tenant_id: str
    customer_id: str
    name: str
    status: str = ""
    customer_type: str = ""
    call_class: str = ""
    account_owner_id: str | None = None


@dataclass(frozen=True)
class ContactReference:
    """Stable contact identity exposed outside CRM."""

    tenant_id: str
    contact_id: str
    customer_id: str
    name: str
    email: str | None = None
    phone: str | None = None
    primary: bool = False


@dataclass(frozen=True)
class CustomerContext:
    """Read-only customer relationship context published by CRM."""

    tenant_id: str
    customer: CustomerReference
    primary_contact: ContactReference | None = None
    last_interaction_at: str | None = None
    next_interaction_at: str | None = None
    open_follow_up_count: int = 0
    potential_summary: str = ""
