# Copilot Instructions

Follow these rules strictly when suggesting code:

- **Clean Architecture:** Adhere to the established layers: Domain, Application, Infrastructure, Presentation.
- **Type Safety:** 
    - TypeScript: Use `strict` mode. NO `any`. Prefer interfaces over types for public APIs.
    - Python: Use strict type hints. Avoid `Any`.
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2 (async).
- **Database:** Always use Alembic for migrations. Never use `metadata.create_all()`.
- **Logic:** Business logic belongs in the `domain` or `application` layers, never in `presentation` (routers) or `infrastructure`.
- **Security:** Never suggest code that logs or stores secrets. Use Pydantic Settings for configuration.
- **Tests:** Always suggest corresponding tests for new logic using `pytest` (backend) or `vitest` (frontend).
- **Documentation:** Refer to `docs/ARCHITECTURE.md` and `AGENTS.md` for context.
