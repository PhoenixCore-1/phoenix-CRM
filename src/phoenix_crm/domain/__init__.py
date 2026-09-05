"""CRM business domain objects."""

from .contact import Contact, ContactStatus
from .customer import CallCadence, Customer, CustomerCallClass, CustomerStatus, CustomerType

__all__ = [
    "CallCadence",
    "Contact",
    "ContactStatus",
    "Customer",
    "CustomerCallClass",
    "CustomerStatus",
    "CustomerType",
]
