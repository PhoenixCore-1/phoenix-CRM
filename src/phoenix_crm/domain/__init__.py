"""CRM business domain objects."""

from .customer import CallCadence, Customer, CustomerCallClass, CustomerStatus, CustomerType

__all__ = [
    "CallCadence",
    "Customer",
    "CustomerCallClass",
    "CustomerStatus",
    "CustomerType",
]
