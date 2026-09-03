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
