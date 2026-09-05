# Phoenix CRM 360 — Phase 9.6 Contacts & Sites

## Status

Phase 9.6 exposes the existing CRM Contacts and Customer Sites domains through a dedicated Customer 360 read section.

## Boundary decisions

- CRM remains authoritative for Contacts and Customer Sites.
- Customer 360 presents these records and does not create a second domain model.
- Primary contact/site is resolved from active CRM records only.
- Records are constrained to the requested tenant and customer.
- Core access scope is enforced when a RequestContext is supplied.
- No dependency is introduced on Projects 360; CRM customer sites remain distinct from project-site authority.
- The projection is read-only and does not mutate contact or site domain objects.

## Verification coverage

Tests cover primary selection, tenant/customer filtering, Core access enforcement, inactive/closed primary handling, deterministic ordering, and read-only behavior.

## Completion criteria

Phase 9.6 is complete when the full CRM test suite passes and the Contacts & Sites section is frozen as part of Customer 360.
