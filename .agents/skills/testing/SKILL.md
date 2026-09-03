# Testing Skill

## Mission
Ensure high code quality and prevent regressions through automated testing.

## Procedure
1. **Locate Tests:**
   - Backend: `src/backend/tests/` (unit, integration, e2e).
   - Frontend: `src/frontend/tests/`.
2. **Write Test:**
   - Use `pytest` for backend.
   - Use `vitest` for frontend.
   - Follow the AAA (Arrange, Act, Assert) pattern.
3. **Run Tests:**
   - Backend: `pytest`
   - Frontend: `npm test`
4. **Verify Coverage:** Ensure new code is covered.

## Constraints
- **Isolation:** Tests should not depend on external services (use mocks/stubs).
- **Determinism:** Tests must be reliable and pass every time.
- **Clean State:** Integration tests must start with a clean database state.

## Definition of Done
- Tests written for the new functionality.
- All tests pass locally.
- No regressions introduced.
