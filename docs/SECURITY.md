# SECURITY.md

## Security First

FinanLove handles sensitive financial data. Security is not an afterthought.

### Core Principles

1. **Never commit secrets:** All credentials must be in `.env` and never pushed to Git.
2. **Secure Hashing:** Use Argon2 or BCrypt for passwords.
3. **JWT Authentication:** Use short-lived access tokens and secure refresh tokens.
4. **Input Validation:** All data entering the system must be validated using Pydantic (Backend) and Zod/TypeScript (Frontend).
5. **Least Privilege:** Database users and API tokens should only have the permissions they need.
6. **No Information Leakage:** Errors in production should not reveal stack traces or internal logic.
7. **CORS:** Explicitly whitelist allowed origins.

### Data Privacy

- User data must be isolated. One user cannot see another's data unless explicitly shared (e.g., in a shared loan).
- Financial values must be handled with high precision (avoid floats, use Decimals).

### Reporting Vulnerabilities

If you find a security bug, please report it directly to the maintainer.
