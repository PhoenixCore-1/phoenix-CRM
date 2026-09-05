"""Application services for Phoenix CRM 360."""

from .activity_timeline import ActivityTimelineEntry, ActivityTimelineService
from .activity_validation import ActivityIntegrityService, ActivityValidationResult
from .ai_intelligence import AIProposal, CRMIntelligenceService, CRMIntelligenceType
from .call_cadence import CadenceResult, CallCadenceService
from .call_plan_timing import CallPlanTiming, CallPlanTimingService, TimedCallPlanItem
from .call_planning import CallPlanItem, CallPlanItemType, CallPlanningService
from .customer_360 import Customer360PurchaseService, Customer360PurchaseView
from .customer_360_contract import Customer360Reference, Customer360View
from .customer_360_overview import Customer360Overview, Customer360OverviewService
from .customer_360_purchase import Customer360PurchaseSection, Customer360PurchaseSectionService
from .customer_360_potential import Customer360PotentialItem, Customer360PotentialSection, Customer360PotentialService, Customer360SolutionItem
from .customer_360_timeline import Customer360Timeline, Customer360TimelineEntry, Customer360TimelineService
from .follow_up_service import FollowUpService
from .lead_access import LeadAccessService
from .lead_activity import LeadActivityContext, LeadActivityService
from .lead_ai import LeadAIContext, LeadAIProposal, LeadAIService, LeadIntelligenceType
from .lead_conversion import CustomerConversionResult, LeadConversionService
from .lead_qualification import LeadQualificationResult, LeadQualificationService
from .lead_matching import LeadMatch, LeadMatchingService
from .potential_qualification import PotentialQualificationResult, PotentialQualificationService
from .potential_service import CustomerPotentialService
from .purchase_history_boundary import PurchaseHistoryBoundary
from .purchase_history_service import PurchaseHistoryProvider, PurchaseHistoryService
from .purchase_summary import PurchaseHistorySummary, PurchaseSummaryService

__all__ = [
    "ActivityIntegrityService",
    "ActivityTimelineEntry",
    "ActivityTimelineService",
    "ActivityValidationResult",
    "AIProposal",
    "CadenceResult",
    "CallCadenceService",
    "CallPlanItem",
    "CallPlanItemType",
    "CallPlanningService",
    "CallPlanTiming",
    "CallPlanTimingService",
    "CRMIntelligenceService",
    "CRMIntelligenceType",
    "Customer360Overview",
    "Customer360OverviewService",
    "Customer360PotentialItem",
    "Customer360PotentialSection",
    "Customer360PotentialService",
    "Customer360PurchaseSection",
    "Customer360PurchaseSectionService",
    "Customer360PurchaseService",
    "Customer360PurchaseView",
    "Customer360Reference",
    "Customer360SolutionItem",
    "Customer360Timeline",
    "Customer360TimelineEntry",
    "Customer360TimelineService",
    "Customer360View",
    "CustomerConversionResult",
    "CustomerPotentialService",
    "FollowUpService",
    "LeadAccessService",
    "LeadActivityContext",
    "LeadActivityService",
    "LeadAIContext",
    "LeadAIProposal",
    "LeadAIService",
    "LeadConversionService",
    "LeadIntelligenceType",
    "LeadMatch",
    "LeadMatchingService",
    "LeadQualificationResult",
    "LeadQualificationService",
    "PotentialQualificationResult",
    "PotentialQualificationService",
    "PurchaseHistoryBoundary",
    "PurchaseHistoryProvider",
    "PurchaseHistoryService",
    "PurchaseHistorySummary",
    "PurchaseSummaryService",
    "TimedCallPlanItem",
]
