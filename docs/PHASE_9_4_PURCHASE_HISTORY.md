# Phoenix CRM 360 — Phase 9.4 Customer 360 Purchase History

## Status

Phase 9.4 exposes the existing Phase 8 purchase-history capability as a dedicated Customer 360 presentation section.

## Boundary decisions

- CRM presents purchase history; it does not own authoritative transactions.
- Customer 360 consumes the existing purchase-history service and boundary.
- No direct dependency is introduced on Sales, Sage, ERP, or another module implementation.
- Purchase history remains optional and degrades gracefully when the provider is unavailable.
- Tenant and customer validation remain enforced by the existing purchase-history boundary and service.
- Customer 360 exposes quantity and relationship-oriented purchase information, not an accounting-level financial total.
- Recent purchases retain the deterministic newest-first ordering from Phase 8.

## Verification coverage

Tests cover summary composition, unavailable-provider degradation, recent-record limits, provider contract mismatch protection, invalid limits, and source-system preservation.

## Completion criteria

Phase 9.4 is complete when the full CRM test suite passes after the implementation and tests are pulled locally. The purchase-history section can then be frozen as the Customer 360 presentation of the existing Phase 8 capability.
