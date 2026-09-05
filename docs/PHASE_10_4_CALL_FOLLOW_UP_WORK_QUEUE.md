# Phase 10.4 — CRM Call & Follow-up Work Queue

## Purpose

Phase 10.4 turns CRM cadence calls and first-class follow-ups into one deterministic, read-only relationship work queue.

## Scope

The queue contains two CRM-owned work item types:

- `call` — generated from the customer's configured call cadence.
- `follow_up` — generated from an active CRM follow-up.

Completed, cancelled and rescheduled follow-ups are not actionable queue items.

## Authority

CRM remains authoritative for customer relationship work. Core remains authoritative for tenant identity and access scope. No Sales, Projects, Inventory or other business-module implementation is required.

## Access and isolation

The service filters records to the requested tenant and applies the Core `RequestContext` resource scope to customers. Related activities and follow-ups are then restricted to visible customers.

## Determinism

Queue ordering is by due timestamp, customer ID, work-item type and follow-up ID. User and temporal filters preserve that ordering.

## Graceful empty state

No customers, no matching cadence configuration, or no active follow-ups produce a valid empty or partial queue rather than an error.

## Non-goals

This phase does not introduce persistence, UI, autonomous task execution, notifications, Sales opportunities, or cross-module dependencies.

## Tests

Focused tests cover call/follow-up composition, terminal follow-up exclusion, tenant/access-scope filtering, user filtering, due/overdue filtering and empty-state behavior.
