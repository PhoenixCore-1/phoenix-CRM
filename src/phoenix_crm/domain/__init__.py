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
from .lead import Lead, LeadSource, LeadStatus
from .potential import CustomerPotential, PotentialPriority, PotentialSource, PotentialStatus
from .potential_solution import CustomerSolution, SolutionRelationship, SolutionStatus
from .purchase_history import PurchaseHistoryContract, PurchaseHistoryRecord, PurchaseRecordStatus
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
    "Contact",
    "ContactStatus",
    "Customer",
    "CustomerActivity",
    "CustomerCallClass",
    "CustomerFollowUp",
    "CustomerSite",
    "CustomerSiteStatus",
    "CustomerSolution",
    "CustomerStatus",
    "CustomerType",
    "FollowUpPriority",
    "FollowUpStatus",
    "InteractionDirection",
    "Lead",
    "LeadSource",
    "LeadStatus",
    "PotentialPriority",
    "PotentialSource",
    "PotentialStatus",
    "ProjectSiteParty",
    "PurchaseHistoryContract",
    "PurchaseHistoryRecord",
    "PurchaseRecordStatus",
    "SitePartyMatchStatus",
    "SitePartyRole",
    "SitePartySource",
    "SitePartyStatus",
    "SolutionRelationship",
    "SolutionStatus",
]
