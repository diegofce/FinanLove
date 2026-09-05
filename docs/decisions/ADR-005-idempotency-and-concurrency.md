# ADR-005: Idempotency and Balance Concurrency

## Status

Accepted

## Context

Retries and concurrent requests can duplicate money movements or overspend an account.

## Decision

Financial endpoints accept `Idempotency-Key`. PostgreSQL stores the key scoped by owner and operation with a unique constraint and a SHA-256 payload fingerprint. Repeated keys with a different fingerprint are conflicts. Requests using the same key are serialized with a PostgreSQL transaction advisory lock. Account balance changes use a conditional update requiring the resulting balance to remain non-negative.

Loan decisions and repayment decisions additionally lock the affected loan and repayment rows with `SELECT ... FOR UPDATE`. This protects outstanding-loan calculations and state transitions when different idempotency keys race on the same loan; the advisory lock alone only serializes requests that reuse the same key.

## Consequences

- Idempotency is durable and process-independent.
- PostgreSQL is required to verify concurrency behavior.
- A client must reuse the same key for a retry of the same logical operation.
- Current local Windows verification is blocked when the host cannot reach the Docker PostgreSQL hostname; CI must run the integration suite.
- CI must execute the PostgreSQL integration suite with `TEST_DATABASE_URL` and `CI=true`; missing PostgreSQL configuration fails in CI instead of silently skipping.
- The integration suite covers concurrent expenses, concurrent transfers, same-key HTTP retries, fingerprint conflicts, rollback, and partial/full loan repayments.

## Alternatives Considered

- In-memory deduplication: rejected because it fails across workers and restarts.
- Read-then-write balance checks: rejected because concurrent requests can both pass the check.
