# ADR-005: Idempotency and Balance Concurrency

## Status

Accepted

## Context

Retries and concurrent requests can duplicate money movements or overspend an account.

## Decision

Financial endpoints accept `Idempotency-Key`. PostgreSQL stores the key scoped by owner and operation with a unique constraint and a SHA-256 payload fingerprint. Repeated keys with a different fingerprint are conflicts. Requests using the same key are serialized with a PostgreSQL transaction advisory lock. Account balance changes use a conditional update requiring the resulting balance to remain non-negative.

## Consequences

- Idempotency is durable and process-independent.
- PostgreSQL is required to verify concurrency behavior.
- A client must reuse the same key for a retry of the same logical operation.
- Current local Windows verification is blocked when the host cannot reach the Docker PostgreSQL hostname; CI must run the integration suite.

## Alternatives Considered

- In-memory deduplication: rejected because it fails across workers and restarts.
- Read-then-write balance checks: rejected because concurrent requests can both pass the check.
