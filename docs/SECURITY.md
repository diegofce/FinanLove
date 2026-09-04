# SECURITY.md

## Security First

FinanLove handles sensitive financial data. Security is not an afterthought.

### Core Principles

1. **Never commit secrets:** All credentials must be supplied through the environment (or a local `.env`) and never pushed to Git. Production requires a unique `JWT_SECRET` with at least 32 characters; the application rejects the development default.
2. **Secure Hashing:** Use Argon2 or BCrypt for passwords.
3. **JWT Authentication:** Use short-lived access tokens and secure refresh tokens.
4. **Input Validation:** All data entering the system must be validated using Pydantic (Backend) and Zod/TypeScript (Frontend).
5. **Least Privilege:** Database users and API tokens should only have the permissions they need.
6. **No Information Leakage:** Errors in production should not reveal stack traces or internal logic.
7. **CORS:** Explicitly whitelist allowed origins.
8. **CSRF on refresh:** `POST /api/v1/auth/refresh` requires an `Origin` header in `CORS_ORIGINS`, or a `Referer` whose origin is in that allowlist. Requests without either header or from another origin return `403`. This protects the HttpOnly refresh-token cookie while retaining browser-based refresh.

9. **Financial idempotency:** Financial requests should send an
   `Idempotency-Key`. The server scopes the key to the authenticated user and
   operation, stores a SHA-256 payload fingerprint, and rejects a reused key
   with a different payload.

10. **Financial concurrency:** Account balance changes use a PostgreSQL
    conditional update that requires the resulting balance to remain
    non-negative. PostgreSQL integration tests are required before claiming
    concurrency behavior is verified.

11. **Access-token lifetime:** Logout revokes the server-side refresh session.
    An already-issued access JWT may remain valid until its short expiration
    because immediate access-token revocation is not implemented.

### Local Compose configuration

Copy `.env.example` to a local environment file and replace all placeholder values. Compose requires `POSTGRES_PASSWORD`, `DATABASE_URL`, and `JWT_SECRET`; it does not embed credentials in the service definition.

### Data Privacy

- User data must be isolated. One user cannot see another's data unless explicitly shared (e.g., in a shared loan).
- Financial values must be handled with high precision (avoid floats, use Decimals).

### Reporting Vulnerabilities

If you find a security bug, please report it directly to the maintainer.
