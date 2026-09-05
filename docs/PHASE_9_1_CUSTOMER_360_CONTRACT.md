# Phoenix CRM 360 — Phase 9.1 Customer 360 Aggregate/View Contract

## Status

Phase 9.1 defines the immutable Customer 360 read contract for Phoenix CRM 360 V1.0.

## Contract boundary

- Customer 360 is a read/presentation model, not a replacement business-domain aggregate.
- CRM remains authoritative for CRM-owned customer relationships and identifiers.
- The contract projects customer identity, classification, ownership, access-scope reference, contact/site references, interaction context, and relationship-health context.
- Related resources owned by CRM or other Phoenix modules are represented by lightweight `Customer360Reference` objects.
- References contain module/resource identifiers and optional display/status information; they do not import or expose another module's implementation.
- The contract is immutable and deterministic for contact/site ID collections.
- No Sales, Projects, Inventory, Production, Procurement, Accounts, Sage, ERP, or other module implementation is required for the contract to exist.

## Phase 9.1 completion criteria

Phase 9.1 is complete when the new contract and hardening tests are pulled locally and the full CRM test suite passes. The contract then becomes the stable foundation for later Customer 360 composition work.
