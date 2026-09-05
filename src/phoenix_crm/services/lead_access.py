"""Core access-scope boundary for Phoenix CRM leads."""

from __future__ import annotations

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import Lead


class LeadAccessService:
    """Consume Core-resolved authorization for CRM lead resources."""

    @staticmethod
    def can_access(lead: Lead, context: RequestContext) -> bool:
        """Return whether Core has granted access to the lead."""
        return (
            context.tenant.tenant_id == str(lead.tenant_id)
            and context.can_access_resource(str(lead.id))
        )

    @staticmethod
    def require_access(lead: Lead, context: RequestContext) -> None:
        """Raise when Core scope does not include the lead."""
        if not LeadAccessService.can_access(lead, context):
            raise PermissionError("Core access scope does not include this lead")

    @staticmethod
    def filter_accessible(
        leads: list[Lead] | tuple[Lead, ...],
        context: RequestContext,
    ) -> tuple[Lead, ...]:
        """Return only tenant-scoped leads explicitly visible in Core scope."""
        return tuple(lead for lead in leads if LeadAccessService.can_access(lead, context))
