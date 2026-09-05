"""CRM business domain objects."""

from .activity import ActivityOutcome, ActivityType, CustomerActivity
from .contact import Contact, ContactStatus
from .customer import CallCadence, Customer, CustomerCallClass, CustomerStatus, CustomerType
from .site import CustomerSite, CustomerSiteStatus
from .site_party import (
    ProjectSiteParty,
    SitePartyMatchStatus,
    SitePartyRole,
    SitePartySource,
    SitePartyStatus,
)

__all__ = [
    "ActivityOutcome",
    "ActivityType",
    "CallCadence",
    "Contact",
    "ContactStatus",
    "Customer",
    "CustomerActivity",
    "CustomerCallClass",
    "CustomerSite",
    "CustomerSiteStatus",
    "CustomerStatus",
    "CustomerType",
    "ProjectSiteParty",
    "SitePartyMatchStatus",
    "SitePartyRole",
    "SitePartySource",
    "SitePartyStatus",
]
