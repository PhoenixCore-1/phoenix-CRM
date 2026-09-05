# Phoenix CRM 360 — Phase 9.5 Potential & Opportunities

## Status

Phase 9.5 exposes CRM-owned customer potential and current/potential solution relationships as a dedicated Customer 360 read section.

## Boundary decisions

- CRM owns customer potential, solution relationships, qualification context and relationship intelligence.
- Sales remains authoritative for commercial opportunities, quotes, pricing, margin and orders.
- This phase does not import or depend on Sales domain classes, persistence, or services.
- Customer 360 presents potential and solution intelligence as read-only projections.
- Terminal potential records and inactive/closed solution relationships are excluded from the active section.
- Tenant and Core access-scope checks remain enforced before composition.
- No mutation or new source of truth is created by the Customer 360 section.

## Completion criteria

Phase 9.5 is complete when the full CRM test suite passes and the section is frozen. Future Sales integration, if required, must use a published contract rather than a direct module dependency.
