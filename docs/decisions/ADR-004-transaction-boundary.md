# ADR-004: Financial Transaction Boundary

## Status

Accepted

## Context

Financial operations update balances, ledger records, notifications, and related entities. Committing from individual routers risks partial state.

## Decision

Use the async SQLAlchemy session dependency as the request transaction boundary. A successful request commits once; an exception rolls the session back. Financial use cases perform all related repository writes through that session. PostgreSQL conditional balance updates reject changes that would create a negative balance.

## Consequences

- Routers do not need to commit successful financial operations individually.
- Integration tests must prove rollback and multi-entity atomicity against PostgreSQL.
- Access-token revocation remains separate from database transaction boundaries.

## Alternatives Considered

- Commit in every repository: rejected because it permits partial financial state.
- Distributed transaction/event system: rejected as unnecessary for the modular monolith.
