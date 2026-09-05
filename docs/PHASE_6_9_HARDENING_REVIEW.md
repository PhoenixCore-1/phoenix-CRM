# Phoenix CRM 360 — Phase 6.9 Hardening Review

## Scope

Phase 6.9 is the final quality gate for the Lead domain. It adds no new business capability.

## Verified boundaries

- Lead lifecycle transitions remain owned by the Lead domain.
- Qualification coordinates domain transitions and does not bypass lifecycle rules.
- Duplicate detection is deterministic, tenant-scoped, and never performs automatic merging.
- Customer conversion requires the potential-customer state and blocks detected customer duplicates unless an explicit review override is supplied.
- Conversion constructs the new Customer before changing the Lead state.
- Core remains the authorization authority. CRM consumes `RequestContext` and does not calculate organizational scope.
- Access checks verify both tenant identity and Core-resolved resource visibility.
- Lead AI assistance remains provider-independent and advisory; AI does not autonomously change Lead state.
- Lead activities use the shared CRM activity architecture rather than a competing domain activity model.
- Module independence is preserved: CRM contains no implementation dependency on Sales, Projects, Production, Inventory, Procurement, or other business modules.

## Regression criteria

The complete pytest suite must remain green before Phase 6 is frozen.

## Explicit non-goals

- No database implementation is introduced by this phase.
- No direct Core database access is introduced.
- No autonomous AI actions are introduced.
- No automatic customer merging is introduced.
- No cross-module persistence dependency is introduced.
