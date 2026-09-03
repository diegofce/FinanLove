# Pull Request Skill

## Mission
Prepare high-quality pull requests for human review.

## Procedure
1. **Self-Review:** Go through your changes and ensure they follow the `AGENTS.md` rules.
2. **Run Lint/Typecheck:**
   - Backend: `ruff check .`, `mypy .`
   - Frontend: `npm run lint`, `npm run typecheck`
3. **Run Tests:** Ensure 100% pass rate.
4. **Draft PR Description:**
   - What changed?
   - Why was it changed?
   - How was it tested?
   - Any breaking changes?

## Definition of Done
- Clean code with no lint/type errors.
- Passing tests.
- Clear and concise documentation of changes.
