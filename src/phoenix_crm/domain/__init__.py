"""CRM business domain objects."""

from .activity import (
    ActivityOutcome,
    ActivitySource,
    ActivityType,
    CustomerActivity,
    InteractionDirection,
)
from .contact import Contact, ContactStatus
from .customer import CallCadence, Customer, CustomerCallClass, CustomerStatus, CustomerType
from .follow_up import CustomerFollowUp, FollowUpPriority, FollowUpStatus
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
    "ActivitySource",
    "ActivityType",
    "CallCadence",
    "CallClass",
    "Contact",
    "ContactStatus",
    "Customer",
    "CustomerActivity",
    "CustomerCallClass",
    "CustomerFollowUp",
    "CustomerSite",
    "CustomerSiteStatus",
    "CustomerStatus",
    "CustomerType",
    "FollowUpPriority",
    "FollowUpStatus",
    "InteractionDirection",
    "ProjectSiteParty",
    "SitePartyMatchStatus",
    "SitePartyRole",
    "SitePartySource",
    "SitePartyStatus",
]
