# Phoenix CRM 360 — Phase 9.9 Customer 360 Integration & Composition

## Status

Phase 9.9 establishes the complete Customer 360 composition layer over the previously frozen Customer 360 sections.

## Composition model

The composition contains the existing read-only sections:

- Customer 360 core view
- Overview
- Activity timeline
- Purchase history
- Potential and solutions
- Contacts and sites
- Projects and sites
- Documents

The composition service does not create a new business-domain aggregate and does not replace the authority of any existing CRM domain service.

## Boundary decisions

- Composition is read-only and immutable.
- Core tenant and access-scope enforcement remains authoritative.
- Every composed section must match the requested tenant and customer.
- Optional capabilities remain gracefully degraded through their existing sections.
- Cross-module information remains lightweight references and published capability boundaries.
- No Sales, Projects, document-storage, or other module implementation is imported by the composition layer.
- The composition layer does not introduce a second persistence model.
- Existing frozen section contracts remain individually usable and testable.

## Customer 360 sequence

`Overview → Activity → Purchases → Potential → Opportunities/References → Contacts → Sites → Projects & Sites → Documents`

Opportunities remain references at this stage; Sales owns the commercial opportunity domain.

## Verification coverage

Tests cover complete composition, customer/view mismatch protection, section tenant/customer mismatch protection, Core access enforcement, optional-section degradation, immutability, and preservation of cross-module references without implementation coupling.

## Completion criteria

Phase 9.9 is complete when the full CRM test suite passes and the composition boundary is frozen as the complete Customer 360 read model.
