# ADR-006: Refresh Sessions and CSRF

## Status

Accepted

## Context

Refresh tokens need persistence and rotation, while an HttpOnly cookie is automatically sent by browsers and therefore requires CSRF consideration.

## Decision

Store only a hash of each refresh token server-side. Issue the raw token in an HttpOnly cookie, rotate it on refresh, reject revoked or reused tokens, and revoke it on logout. Refresh requires an allowed `Origin` or `Referer` origin from configured CORS origins. Access JWTs remain short-lived and are not immediately revoked by logout.

## Consequences

- Refresh cookies are not usable by JavaScript.
- CSRF protection is tied to the configured browser origins.
- A stolen access JWT remains valid until expiration; this is documented and accepted for the current phase.
- Endpoint-level refresh/reuse tests require the PostgreSQL integration environment.

## Alternatives Considered

- Refresh tokens in localStorage: rejected because of XSS exposure.
- Immediate access-token blacklist: deferred as unnecessary complexity for the current monolith.
