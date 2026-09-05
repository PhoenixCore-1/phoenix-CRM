"""Customer 360 project/site references and CRM site-party relationships."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from phoenix_crm.api import RequestContext
from phoenix_crm.domain import ProjectSiteParty, SitePartyStatus
from phoenix_crm.services.customer_360_contract import Customer360Reference


@dataclass(frozen=True, slots=True)
class Customer360ProjectSiteSection:
    """Read-only Projects & Sites section for Customer 360."""

    tenant_id: UUID
    customer_id: UUID
    projects: tuple[Customer360Reference, ...]
    project_sites: tuple[Customer360Reference, ...]
    site_parties: tuple[Customer360Reference, ...]


class ProjectReferenceProvider(Protocol):
    """Published capability for resolving project references for a customer."""

    def references_for_customer(self, *, tenant_id: UUID, customer_id: UUID) -> tuple[Customer360Reference, ...]:
        ...


class Customer360ProjectsService:
    """Compose project/site references without depending on Projects implementation."""

    @staticmethod
    def build(
        *,
        tenant_id: UUID,
        customer_id: UUID,
        project_references: tuple[Customer360Reference, ...] = (),
        project_site_references: tuple[Customer360Reference, ...] = (),
        site_parties: tuple[ProjectSiteParty, ...] = (),
        provider: ProjectReferenceProvider | None = None,
        request_context: RequestContext | None = None,
    ) -> Customer360ProjectSiteSection:
        Customer360ProjectsService._require_access(tenant_id, customer_id, request_context)
        if provider is not None:
            project_references = provider.references_for_customer(
                tenant_id=tenant_id, customer_id=customer_id
            )

        projects = Customer360ProjectsService._filter_refs(
            project_references, tenant_id, customer_id, "project"
        )
        project_sites = Customer360ProjectsService._filter_refs(
            project_site_references, tenant_id, customer_id, "project_site"
        )
        parties = tuple(
            Customer360Reference(
                module_code="crm",
                resource_type="project_site_party",
                resource_id=item.id,
                label=item.name,
                status=item.status.value,
            )
            for item in site_parties
            if item.tenant_id == tenant_id
            and item.customer_id == customer_id
            and item.status is SitePartyStatus.ACTIVE
        )
        return Customer360ProjectSiteSection(
            tenant_id=tenant_id,
            customer_id=customer_id,
            projects=projects,
            project_sites=project_sites,
            site_parties=parties,
        )

    @staticmethod
    def _filter_refs(
        references: tuple[Customer360Reference, ...],
        tenant_id: UUID,
        customer_id: UUID,
        resource_type: str,
    ) -> tuple[Customer360Reference, ...]:
        del tenant_id, customer_id
        return tuple(
            sorted(
                (item for item in references if item.resource_type == resource_type),
                key=lambda item: (item.label or "").lower(),
            )
        )

    @staticmethod
    def _require_access(tenant_id: UUID, customer_id: UUID, request_context: RequestContext | None) -> None:
        if request_context is None:
            return
        if request_context.tenant.tenant_id != str(tenant_id):
            raise PermissionError("Core access scope does not include this customer")
        if not request_context.can_access_resource(str(customer_id)):
            raise PermissionError("Core access scope does not include this customer")
