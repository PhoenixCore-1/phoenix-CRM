# Phoenix CRM 360 — Phase 10.1 Dashboard Foundation

## Status

Phase 10.1 establishes the dashboard foundation and contract only. KPI calculations and work-queue behavior remain subsequent Phase 10 work.

## Scope

The dashboard foundation provides immutable read-only contracts for:

- dashboard metrics/cards;
- dashboard sections;
- tenant-aware dashboard composition;
- deterministic section and metric ordering supplied by the caller;
- optional/unavailable sections for graceful degradation.

## Architecture

`CustomerDashboardFoundationService` is deliberately thin. It does not calculate CRM business KPIs and does not own customer, activity, follow-up, purchase, project, Sales, Inventory, or document data.

Later dashboard phases must consume existing CRM services and published capabilities rather than duplicate domain logic.

Core remains authoritative for tenant and access scope. When a `RequestContext` is supplied, the foundation verifies that its tenant matches the requested dashboard tenant. User-specific authorization remains a Core responsibility.

## Contract

`CustomerDashboardMetric` contains a stable key, display label, semantic metric kind, value, and availability flag.

`CustomerDashboardSection` contains a stable key, display label, ordered immutable metrics, and availability flag.

`CustomerDashboardFoundation` contains tenant/user identity and ordered immutable sections.

## Deliberate non-goals

Phase 10.1 does not freeze the final CRM KPI set, implement the work queue, add UI, connect Sales, connect Projects, or introduce a persistence/reporting subsystem.

## Verification

Seven focused tests cover structure, empty-state behavior, duplicate-key protection, Core tenant enforcement, graceful unavailable sections, and immutability.
