## Overview

Warkop SaaS is a Django and Django REST Framework backend project designed as a multi-tenant management system for warkop (coffee shop) businesses.

I built this project to demonstrate **backend engineering depth rather than feature breadth**. The scope is intentionally kept small, allowing each core workflow and architectural decision to be approached with deliberate reasoning, explicit trade-offs, and a strong focus on security, correctness, and testability. The project focuses on problems such as tenant isolation, authorization boundaries, transaction management, concurrency control, historical data, audit trails, and query design.

The goal is not to build a massive application or collect technologies for the sake of appearance, but to demonstrate how to design and build a **secure, consistent, defensible, and testable backend system** under realistic business and security constraints.


## Architecture

Warkop SaaS follows a layered backend architecture designed to keep HTTP concerns separate from business logic and data access.

```text
HTTP Request
    ↓
View
    ↓
Serializer
    ↓
DTO (when meaningful)
    ↓
Service / Use Case
    ↓
ORM / PostgreSQL
    ↓
Response Serializer
    ↓
HTTP Response
```

Each layer has a clear responsibility. Views orchestrate HTTP requests and responses, serializers define the HTTP input/output contract, DTOs provide explicit application contracts for sufficiently complex use cases, and services enforce business rules, authorization, tenant isolation, transactions, and concurrency control.

This separation is intentional rather than pattern-driven. Simpler CRUD operations can use Django REST Framework's generic views directly, while complex business workflows are handled explicitly through API views and application services. The goal is to keep the architecture understandable while still providing clear boundaries for security, correctness, and future change.


## Multi-Tenancy & Security

Warkop SaaS is designed as a multi-tenant backend where multiple warkop businesses share the same application while their data remains isolated.

Tenant context is established from the authenticated request and resolved into an active `TenantMembership`. Business operations use this membership as the trusted actor context rather than relying on tenant or role information supplied by the client.

Tenant isolation is enforced at the data-access layer through tenant-aware managers and explicit tenant scoping in critical queries. Resource lookups are scoped to the actor's tenant so that cross-tenant resources are not treated as valid inputs to business workflows.

Authorization is enforced at two boundaries. DRF permissions protect the HTTP entry point, while application services enforce business-level authorization independently of the transport layer. This ensures that business rules remain effective even when a service is invoked outside an HTTP request.

The system also follows a defense-in-depth approach: client-controlled identifiers are treated as intent, not authority. The server determines the actor, tenant scope, current resource state, and resulting state before applying a business operation.

## Transactions & Concurrency

Several core workflows in Warkop SaaS perform multiple related database mutations that must remain consistent. For these workflows, database transactions are used to ensure that either the complete operation succeeds or all changes are rolled back.

For example, creating an order affects multiple pieces of state at once:

```text
Order
+ OrderItem
+ Product.stock
+ StockMovement
```

These changes are executed within a single transaction so that a failure during the workflow cannot leave partially persisted business state.

Transactions are also used together with row-level locking when the correctness of a decision depends on mutable database state. Stock-related operations use `select_for_update()` to ensure that concurrent requests do not make decisions based on the same stale stock value.

For example, if two orders attempt to purchase the last available units of the same product concurrently, one transaction acquires the product row lock first. The second transaction waits until the first commits, then evaluates the stock against the updated state.

Where multiple product rows can be locked within the same workflow, product IDs are processed in a canonical order. This reduces the risk of deadlocks caused by concurrent transactions acquiring the same set of locks in different orders.

The project deliberately distinguishes transaction boundaries from locking. `transaction.atomic()` provides atomicity, while `select_for_update()` provides concurrency control. Neither mechanism is introduced merely because a function is labeled as a service; they are used when the underlying business workflow requires them.


## Historical Data & Audit Trail

Warkop SaaS distinguishes between **current state** and **historical truth**. Current product data represents how the catalog looks now, while transaction records must preserve what was true at the time an operation occurred.

For example, `OrderItem` stores the product name and price at the time of the transaction rather than relying on the current `Product` record. This prevents later catalog changes from altering the meaning of historical orders.

Inventory changes are recorded through `StockMovement`, which acts as an immutable audit trail while `Product.stock` represents the current inventory state. Each movement records the direction, quantity, reason, actor, and timestamp of the change.

This separation also allows archived products to remain meaningful in historical workflows. Archiving changes the product's current catalog availability, but it does not invalidate transactions or historical inventory events that already reference the product.

When a historical correction is required, the system records a new corrective movement instead of editing or deleting the original event. This preserves the sequence of what actually happened and keeps the audit trail trustworthy.




## Business Rules & State Management
Business operations in the system are treated as explicit state transitions rather than generic data updates. For instance, transitioning an order to `VOID` is a dedicated business command that evaluates the current lifecycle state, applies specific role authorizations, and restores product inventory.

Role authorization is deeply integrated into the service layer rather than relying solely on HTTP endpoint permissions. For example, an `ORDER_VOID` operation requires `OWNER` or `MANAGER` authority, while a `CASHIER` is explicitly forbidden from performing inventory-sensitive restorations. By maintaining these rules at the business boundary, the application guarantees that business invariants are respected regardless of how the workflow is invoked


## Testing

The project uses `pytest` and `pytest-django` with a focus on **business behavior and security invariants rather than implementation details**.

The test suite covers the core workflows and their failure modes, including:

* tenant isolation and cross-tenant access prevention
* role-based authorization and membership lifecycle rules
* product and inventory business rules
* order creation, payment, and void state transitions
* transactional rollback across multi-model mutations
* concurrency scenarios involving stock mutations and order state changes
* timezone-aware reporting and business-day boundaries
* historical transaction snapshots and inventory audit behavior

Concurrency tests use deterministic synchronization techniques such as thread barriers and explicit database connection handling to verify the resulting database state under simultaneous requests.

Failure-path tests also verify persisted state after an exception, ensuring that rejected or failed operations do not leave partial business mutations behind.

The goal of the test suite is not to maximize test count, but to provide evidence that important business and security invariants hold under both normal and adversarial conditions.



## Key Engineering Decisions

### 1. Tenant Isolation as a Security Invariant

Tenant isolation is treated as a core security invariant rather than an application-level convention.

Tenant context is derived from the authenticated user's active membership, and critical resource queries are scoped to that tenant. Tenant-aware managers provide a safe default access path, while explicit tenant scoping is retained in critical workflows as a defense-in-depth measure.

This prevents client-controlled identifiers from becoming implicit authorization and ensures that cross-tenant resources are not treated as valid application state.

### 2. Transactions and Row-Level Locking for State Integrity

Transactions and row-level locking are used selectively based on the business operation being performed.

Multi-model workflows such as order creation and order voiding use `transaction.atomic()` to ensure that related state changes either commit together or roll back together. Operations that make decisions based on mutable state, such as inventory changes and concurrent order processing, use `select_for_update()` to serialize access to the relevant rows.

The project deliberately distinguishes atomicity from concurrency control rather than treating them as interchangeable mechanisms.

### 3. Historical Truth Is Stored Explicitly

The system separates mutable current state from historical transaction data.

`Product` represents current catalog and inventory state, while `OrderItem` stores transaction-time product information and `StockMovement` records inventory events as an immutable audit trail.

This prevents later changes to the catalog from rewriting the meaning of historical transactions and allows inventory history to remain trustworthy even when products are archived.


### 4. Explicit Application Contracts Where Complexity Justifies Them

DTOs are used selectively rather than for every service.

For complex use cases such as order creation, a DTO provides an explicit application contract between the HTTP layer and the service layer. It allows the service to remain independent of DRF while making the expected input structure clear and validated.

Simpler operations intentionally avoid DTOs when the additional abstraction would not provide meaningful value. This keeps the architecture explicit without introducing ceremony for its own sake.

### 5. Infrastructure Follows Workload

The project intentionally does not include infrastructure such as Redis or Celery without a workload that requires asynchronous processing.

They were removed from the current architecture because no existing business workflow required background execution. This keeps the project smaller and easier to reason about while leaving room to introduce asynchronous processing when a concrete requirement—such as a large report export—actually justifies it.


## Tech Stack & Scope

### Stack

* Python
* Django
* Django REST Framework
* PostgreSQL
* pytest
* pytest-django

### Scope

Warkop SaaS intentionally focuses on a small set of core coffee shop workflows rather than trying to model a complete POS or commercial SaaS platform.

The implemented scope covers:

* multi-tenant tenant and membership management
* product and inventory management
* order creation and lifecycle operations
* stock movement and audit history
* timezone-aware operational reports

The project deliberately excludes concerns that are outside its engineering focus, such as payment gateway integration, asynchronous infrastructure, distributed services, and real-time communication.

