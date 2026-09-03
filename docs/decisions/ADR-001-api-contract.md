# ADR-001: API Contract Strategy

## Status
Proposed

## Context
We need a way to maintain consistency between the Backend (Python/FastAPI) and the Frontend (TypeScript/React) without manual duplication of models.

## Decision
The FastAPI backend will be the **Single Source of Truth** for the API contract.
- FastAPI will generate an `openapi.json` specification automatically.
- We will use OpenAPI as the bridge to generate TypeScript types/clients for the frontend.

## Consequences
- **Pros:** No manual type synchronization, reduced risk of breaking changes, "Contract-First" feel with implementation speed.
- **Cons:** Requires a generation step in the development workflow.

## Alternatives Considered
- Manual duplication: Rejected (error-prone).
- Shared JSON Schemas: Rejected (too much overhead).
