# FinanLove Backend API

Clean Architecture implementation of the FinanLove API.

## Structure

- `app/domain`: Business logic and entities.
- `app/application`: Use cases.
- `app/infrastructure`: DB and external services.
- `app/presentation`: FastAPI routers and schemas.
- `app/core`: Configuration and security.

## Setup

```bash
pip install -e ".[dev]"
```

## Run

```bash
uvicorn app.main:app --reload
```

## Integration tests

The integration suite requires an explicit PostgreSQL `TEST_DATABASE_URL` using
the async SQLAlchemy driver, for example:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/finanlove_test \
	pytest tests/integration -q
```

The shared fixture runs `alembic upgrade head` against that controlled database.
It does not drop or truncate tables and skips database-backed tests explicitly
when `TEST_DATABASE_URL` is absent. Tests create uniquely named records, so CI
should provide a disposable test database or an isolated database/schema. The
local verification on Windows was limited to the explicit skip path because no
PostgreSQL service was available at the configured host.
