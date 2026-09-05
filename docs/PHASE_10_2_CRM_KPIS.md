# Phoenix CRM 360 V1.0 — Phase 10.2 CRM KPI Definitions & Calculations

## Status

Phase 10.2 establishes the first CRM-owned dashboard KPI definitions and deterministic calculations. It builds on the frozen Phase 10.1 dashboard contract.

## KPI definitions

The KPI snapshot currently defines:

- Total Customers
- Active Customers
- Prospects
- On Hold Customers
- Inactive Customers
- Closed Customers
- New Leads
- Potential Customers
- Active Potential
- Open Follow-ups
- Overdue Follow-ups
- Calls Due
- Recent Activities
- Customers by Type
- Customers by Call Class

`Calls Due` includes CRM call-cadence contacts whose calculated next interaction is at or before the supplied reference time, plus open follow-ups whose due time has arrived. The calculation is deterministic because callers provide `reference_at`.

`Recent Activities` defaults to a 30-day window and is calculated against the supplied reference time. The window is configurable but must be positive.

## Ownership and authority

CRM is authoritative for these relationship KPIs. The KPI service consumes CRM domain records and published CRM services only. It does not query Sales, Projects, Inventory, Procurement, Accounts, Sage, or another module's private persistence.

Purchase and financial values are intentionally absent because CRM is not the financial source of truth.

## Access and tenancy

The service filters all supplied records to the requested tenant. When a Core `RequestContext` is supplied, customer metrics are additionally limited to resources allowed by Core's resolved access scope. A mismatched Core tenant is rejected.

## Dashboard contract integration

`CustomerDashboardKPIs.as_dashboard_sections()` renders KPI values through the immutable Phase 10.1 `CustomerDashboardSection` and `CustomerDashboardMetric` contracts. Phase 10.1 remains the structural contract; Phase 10.2 supplies CRM-owned calculations.

## Determinism and empty state

- Counts are derived from explicit lifecycle statuses.
- Distributions are sorted deterministically by display label.
- Missing customer type/call-class configuration falls back to the configured identifier rather than dropping the customer.
- Empty input produces valid zero-valued KPI results.
- No current-time dependency is used when calculating KPI windows or call due status; `reference_at` is required.

## Non-goals

Phase 10.2 does not implement the dashboard UI, work-queue interaction model, reporting, Sales integration, Projects integration, financial reporting, persistence, or AI KPI interpretation.
