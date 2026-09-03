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
