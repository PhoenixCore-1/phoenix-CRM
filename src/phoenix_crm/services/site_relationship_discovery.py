"""Project/site relationship discovery service for Phoenix CRM 360."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_crm.domain import ProjectSiteParty, SitePartyRole, SitePartySource


@dataclass(frozen=True, slots=True)
class ProjectSiteReference:
    """Reference to an authoritative project/site owned by Projects 360."""

    project_id: UUID
    project_site_id: UUID
    tenant_id: UUID


class SiteRelationshipDiscoveryService:
    """Record parties discovered against an external project site.

    Projects 360 remains authoritative for project and project-site entities.
    CRM only records relationship intelligence about parties discovered there.
    """

    def discover_party(
        self,
        site: ProjectSiteReference,
        name: str,
        role: SitePartyRole,
        *,
        source: SitePartySource = SitePartySource.PROJECT_SITE_DISCOVERY,
        notes: str | None = None,
    ) -> ProjectSiteParty:
        """Create a CRM relationship record for a discovered site party."""
        self.validate_site_reference(site)
        return ProjectSiteParty(
            tenant_id=site.tenant_id,
            project_id=site.project_id,
            project_site_id=site.project_site_id,
            name=name,
            role=role,
            source=source,
            notes=notes,
        )

    @staticmethod
    def is_duplicate(
        existing: list[ProjectSiteParty],
        candidate: ProjectSiteParty,
    ) -> bool:
        """Return whether the same party/role already exists for the site."""
        candidate_name = " ".join(candidate.name.casefold().split())
        return any(
            party.tenant_id == candidate.tenant_id
            and party.project_id == candidate.project_id
            and party.project_site_id == candidate.project_site_id
            and party.role is candidate.role
            and " ".join(party.name.casefold().split()) == candidate_name
            for party in existing
        )

    @staticmethod
    def validate_site_reference(site: ProjectSiteReference) -> None:
        """Validate that an external project/site reference is complete."""
        if site.tenant_id.int == 0:
            raise ValueError("Site reference tenant ID cannot be empty")
        if site.project_id.int == 0:
            raise ValueError("Project reference ID cannot be empty")
        if site.project_site_id.int == 0:
            raise ValueError("Project site reference ID cannot be empty")
