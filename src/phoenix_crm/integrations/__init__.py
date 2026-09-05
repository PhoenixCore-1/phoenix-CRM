"""Integration boundaries for Phoenix CRM 360."""

from .platform import CRMPlatformAdapter
from .runtime import (
    CRMPublishedCapabilityHandler,
    CRMCustomerCapabilityProvider,
)

__all__ = [
    "CRMPlatformAdapter",
    "CRMPublishedCapabilityHandler",
    "CRMCustomerCapabilityProvider",
]
