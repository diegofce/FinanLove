# ADR-003: Frontend Architecture

## Status
Proposed

## Context
The frontend needs to be modular to handle various financial features (Transactions, Loans, Goals) independently.

## Decision
We will use a **Feature-Based Architecture**.

Structure:
- `src/features/` will contain self-contained modules (e.g., `features/auth`, `features/transactions`).
- Each feature folder contains its own components, hooks, services, and types.
- Shared components go into `src/components`.

## Consequences
- **Pros:** Easier to navigate, isolated features, promotes reuse.
- **Cons:** Slightly more complex directory structure.

## Alternatives Considered
- Type-based (folders like `components/`, `hooks/` only): Rejected (hard to manage as the app grows).
