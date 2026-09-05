# Phoenix CRM 360 — Phase 9.2 Customer 360 Overview

## Status

Phase 9.2 implements the CRM-owned Customer 360 overview composition layer.

## Purpose

The overview provides a concise, read-only relationship snapshot assembled from existing CRM domain objects. It does not create a second customer aggregate or duplicate ownership of the underlying domains.

## Included overview signals

- Customer 360 view contract.
- Activity count and last activity timestamp.
- Open follow-up count.
- Overdue open follow-up count.
- Active customer-potential count.
- Active current-solution count.
- Active potential-solution count.

## Boundary decisions

- Customer remains the CRM customer authority.
- Activities, follow-ups, potentials, and solutions remain owned by their existing CRM domains.
- The overview is read-only and composes supplied domain data.
- Records are filtered to the requested tenant and customer.
- Core remains authoritative for tenant and access-scope enforcement when a RequestContext is supplied.
- No direct dependency is introduced on Sales, Projects, Inventory, Procurement, Production, or other module implementations.
- Cross-module information continues to use the Customer 360 contract/reference boundary.

## Verification coverage

Phase 9.2 tests cover:

1. Overview composition and core customer counts.
2. Tenant/customer isolation of supplied records.
3. Open follow-up filtering.
4. Overdue follow-up detection.
5. Active potential filtering.
6. Current/potential solution counts.
7. Customer/view consistency.
8. Core access-scope enforcement.

## Completion criteria

Phase 9.2 is complete when the full CRM test suite passes after the implementation is pulled locally. The overview is then frozen as the read-only composition layer for the Customer 360 experience.
