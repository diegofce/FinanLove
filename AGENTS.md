# FINANLOVE — AGENT OPERATING INSTRUCTIONS

## Mission

FinanLove is a professional personal and shared financial management application. This repository is designed to be highly structured, strictly typed, and "agent-friendly", allowing AI agents and human developers to collaborate efficiently within a Clean Architecture framework.

## Source of Truth

1. `docs/SPEC.md`: Functional requirements and business rules.
2. `docs/ARCHITECTURE.md`: Technical design and architectural patterns.
3. `docs/decisions/*.md`: Architectural Decision Records (ADRs).
4. `AGENTS.md`: This document (operational instructions).

## Golden Rules

- **No Architecture Sprawl:** Do not invent new architectural patterns. Follow the established Clean Architecture.
- **Strict Tech Stack:** Do not introduce new libraries or frameworks without authorization.
- **Layer Integrity:** Never skip layers. `Presentation -> Application -> Domain`. `Infrastructure -> Application/Domain`.
- **Database Safety:** No direct DB access from routers. Use repositories. No `create_all()` in production; use Alembic migrations.
- **Environment Safety:** Do not modify `.env` directly. Use `.env.example` as a template. Never commit secrets.
- **Type Safety:** `any` is forbidden in TypeScript. Use strict type hints in Python.
- **Quality Guardrails:** Never delete or skip tests to fix CI. Do not disable linters.
- **Atomic Changes:** Keep changes focused and documented.

## Agent Workflow (Mandatory)

BEFORE MODIFYING:
1. **Inspect:** Analyze the current structure and relevant files.
2. **Read:** Consult `AGENTS.md` and related documentation.
3. **Locate:** Find the code to be modified and its dependencies.
4. **Plan:** Propose a plan before execution.

DURING IMPLEMENTATION:
5. **Implement:** Write code following project conventions.
6. **Test:** Run existing tests and add new ones for the change.
7. **Lint/Typecheck:** Ensure code meets quality standards.

AFTER IMPLEMENTATION:
8. **Review:** Check the diff for unintended changes or secrets.
9. **Report:** Clearly state what was changed and why.

## Definition of Done

A task is complete ONLY when:
- Code is implemented following Clean Architecture.
- Unit/Integration tests pass.
- Linting (Ruff/ESLint) and Type Checking (MyPy/TSC) are clean.
- Documentation (if applicable) is updated.
- Migrations are created (if DB schema changed).
- No secrets are exposed.
- Diff has been self-reviewed.
