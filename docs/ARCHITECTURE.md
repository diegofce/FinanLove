# ARCHITECTURE.md

## Overview

FinanLove is built as a **Modular Monolith** using **Clean Architecture** principles. This ensures that business logic remains independent of frameworks, databases, and external tools.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (Async), Pydantic v2, Alembic.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query.
- **Database:** PostgreSQL.
- **Infrastructure:** Docker, Docker Compose, GitHub Actions.

## Backend Layers

### 1. Domain Layer (`src/backend/app/domain`)

- **Responsibility:** Contains core business entities, value objects, and business rules.
- **Dependencies:** None. It should not depend on any framework or library (except for basic types).

### 2. Application Layer (`src/backend/app/application`)

- **Responsibility:** Implements Use Cases (Interactors). It coordinates the domain entities and calls the repository interfaces.
- **Dependencies:** Domain.

### 3. Infrastructure Layer (`src/backend/app/infrastructure`)

- **Responsibility:** Implements interfaces defined in Application/Domain (e.g., Database repositories, Email services).
- **Dependencies:** Application, Domain.

### 4. Presentation Layer (`src/backend/app/presentation`)

- **Responsibility:** Handles HTTP requests, input validation (Pydantic), and formatting responses.
- **Dependencies:** Application, Domain.

## Frontend Layers

- **Features (`src/features/`):** Business-specific modules (Auth, Transactions, etc.).
- **Components (`src/components/`):** Shared UI components.
- **Services (`src/services/`):** API client logic.
- **Store (`src/app/store.ts`):** Global state management (if needed).

## Dependency Rule

Dependencies always point **inwards**:
`Presentation -> Application -> Domain`
`Infrastructure -> Application -> Domain`

## Data Flow

1. Request hits FastAPI router (**Presentation**).
2. Router validates input and calls a Use Case (**Application**).
3. Use Case interacts with Entities (**Domain**) and Repositories (**Infrastructure**).
4. Use Case returns a result.
5. Router formats the result and returns it as JSON.

## Security

- JWT for authentication.
- Argon2 for password hashing.
- Strict CORS policies.
- Pydantic Settings for environment management.

## Financial Transaction Boundary

Database-backed requests use an async SQLAlchemy unit of work exposed by the
database dependency. A successful request commits once; an exception rolls the
session back. Financial use cases update balances and ledger records in the
same session. PostgreSQL conditional balance updates reject an expense that
would make an account negative.

Idempotent financial requests use a PostgreSQL unique key scoped by user and
operation, plus a SHA-256 payload fingerprint. Advisory transaction locks
serialize requests using the same key. The concurrency and rollback contract
is covered by integration tests in `src/backend/tests/integration`; those tests
require PostgreSQL and are executed by CI.

## Sessions and CSRF

Access JWTs are short-lived. Refresh tokens are hashed and persisted, rotated
on refresh, revoked on logout, and delivered in an HttpOnly cookie. Refresh
requests require an allowed `Origin` or `Referer` value because the cookie is
automatically sent by browsers. An access JWT already issued remains valid
until expiry because access-token revocation is not implemented.
