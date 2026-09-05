# Phoenix CRM 360 V1.0

Phoenix CRM 360 is a modular business application running on Phoenix Core V2.0.

## Purpose

CRM owns the customer relationship and customer-development domain: customers, contacts, customer types, customer call classes and cadence, activities, follow-ups, call planning, customer potential, relationship history, and references to business information owned by other Phoenix modules.

## Architecture

Phoenix CRM 360 is a business module, not a standalone platform. It integrates with Phoenix Core through defined module contracts and does not bypass Core security, tenancy, permissions, audit, licensing, or integration boundaries.

Core provides the platform-wide organizational and access-scope model. CRM consumes Core-resolved access scope and does not implement an independent customer visibility model.

Projects and Sites are owned by Phoenix Projects 360. CRM stores relationship/reference information so project and site participants can be matched to existing customers or captured as potential leads without duplicating Project/Site authority.

Purchase transactions remain authoritative in Phoenix Sales 360 and/or the configured financial authority. CRM presents customer purchase history as part of Customer 360 without becoming a second transactional source of truth.

The Solutions Engine may provide customer potential and solution recommendations. CRM records and surfaces that potential, while active commercial opportunities and transactions remain with the appropriate business module.

## V1.0 Principles

- Manufacturer-agnostic
- Tenant-aware
- Permission-controlled
- Auditable
- API/contract based
- No direct access to another module's private persistence
- Core access scope is authoritative for resource visibility
- Projects 360 owns project/site records
- Sales 360 remains authoritative for sales transactions
- AI assists within explicit authority boundaries

## Development

Python 3.11+ is required. The initial test dependency is pytest 8.x.

The repository is built incrementally. Business domains are added only after the module foundation and integration contracts are verified.
