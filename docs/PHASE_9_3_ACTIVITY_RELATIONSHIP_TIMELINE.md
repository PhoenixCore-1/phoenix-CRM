# Phoenix CRM 360 — Phase 9.3 Activity & Relationship Timeline

## Status

Phase 9.3 adds the Customer 360 relationship timeline as a read-only presentation service over the existing CRM activity domain.

## Boundary decisions

- CRM activities remain authoritative within the CRM activity domain.
- Customer 360 consumes activities; it does not create a second activity store.
- Timeline entries are presentation/read-model objects and do not mutate activities.
- Timeline filtering is tenant- and customer-scoped.
- Core remains authoritative for tenant and access-scope authorization.
- Activity direction, source, outcome, contact, user, duration, and communication reference are preserved where supplied by the activity domain.
- Ordering is newest-first and delegated to the existing deterministic activity-history behavior.
- An optional limit is applied after chronological ordering.
- No dependency is introduced on Sales, Projects, Inventory, Procurement, or other module implementations.

## Verification coverage

Tests cover newest-first ordering, activity metadata projection, tenant/customer filtering, Core tenant and resource scope enforcement, post-order limit application, invalid limits, input immutability, and empty timelines.

## Completion criteria

Phase 9.3 is complete when the full CRM test suite passes with the timeline implementation and tests pulled locally. The timeline can then be frozen as the Customer 360 presentation layer over the existing activity history.
