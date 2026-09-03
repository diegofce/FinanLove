# ADR-002: Backend Architecture

## Status
Proposed

## Context
FinanLove needs a maintainable, testable, and scalable backend that can grow from a personal tool to a SaaS.

## Decision
We will use a **Pragmatic Clean Architecture** organized as a **Modular Monolith**.

Layers:
1. **Domain:** Business entities, value objects, and core rules. No dependencies.
2. **Application:** Use cases that coordinate domain and infrastructure.
3. **Infrastructure:** Concrete implementations (DB with SQLAlchemy, Email, etc.).
4. **Presentation:** FastAPI routers, schemas (Pydantic), and dependency injection.

## Consequences
- **Pros:** High testability, decoupled business logic, clear boundaries.
- **Cons:** More boilerplate initially than a standard FastAPI "all-in-one" approach.

## Alternatives Considered
- Standard Layered (MVC): Rejected (business logic often leaks into controllers/models).
- Microservices: Rejected (overkill for the current scale).
