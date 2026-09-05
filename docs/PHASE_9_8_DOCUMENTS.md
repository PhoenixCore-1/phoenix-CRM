# Phoenix CRM 360 — Phase 9.8 Documents

## Status

Phase 9.8 exposes customer documents as a read-only Customer 360 presentation section through an optional published document capability.

## Boundary decisions

- Customer 360 presents documents; it does not own document storage or file-management infrastructure.
- Document resolution is provider-independent and contract-based.
- The document capability is optional. When unavailable, Customer 360 returns an empty Documents section with `available=False`.
- Document references are lightweight `Customer360Reference` values; Customer 360 does not import another module's document implementation or persistence.
- Only document resource types (`document` and `customer_document`) are presented.
- Core tenant and access-scope checks are enforced before composition.
- The projection is read-only and does not mutate document references.
- Future document integrations must use a published Phoenix capability and preserve independent module operation.

## Verification coverage

Tests cover document projection, non-document filtering, Core access enforcement, unavailable-capability degradation, optional provider integration, deterministic ordering, and read-only behavior.

## Completion criteria

Phase 9.8 is complete when the full CRM test suite passes and the Documents section is frozen as part of Customer 360.
