# Phoenix CRM 360 — Phase 9.7 Projects & Sites

## Status

Phase 9.7 exposes project and project-site relationships as read-only Customer 360 references and surfaces CRM-owned site-party relationships.

## Boundary decisions

- Phoenix Projects 360 remains authoritative for Projects and Project Sites.
- CRM stores only relationship intelligence and lightweight external references.
- Customer 360 consumes published references/capabilities rather than Projects domain classes, repositories, persistence, or private services.
- Project capability is optional; when unavailable, Customer 360 returns an empty Projects & Sites section.
- CRM site parties remain CRM-owned relationship records and reference the external project/project-site IDs without duplicating those entities.
- Only active site-party relationships matched to the requested customer are presented.
- Tenant and Core access-scope checks are enforced before composition.
- The section is read-only and does not mutate project references or CRM site-party records.

## Completion criteria

Phase 9.7 is complete when the full CRM test suite passes and the Projects & Sites section is frozen. Any future Projects integration must use a published Phoenix contract/capability and must preserve independent module operation.
