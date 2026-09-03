# Database Migrations Skill

## Mission
Manage database schema changes safely using Alembic.

## Procedure
1. **Define the Model:** Create or update your SQLAlchemy model in `src/backend/app/domain/entities.py` (or specific entity file).
2. **Generate Migration:**
   ```bash
   cd src/backend
   alembic revision --autogenerate -m "description of change"
   ```
3. **Review Migration:** Inspect the generated file in `src/backend/alembic/versions/`. Ensure it does what you expect and handles edge cases (like existing data).
4. **Apply Migration:**
   ```bash
   alembic upgrade head
   ```

## Constraints
- **NO destructuve changes:** Avoid `DROP TABLE` or `DROP COLUMN` unless explicitly requested.
- **Rollback Plan:** Always ensure there's a corresponding `downgrade` path in the migration.
- **Async Support:** Ensure migrations work with the async engine configuration.

## Definition of Done
- Migration file created and reviewed.
- Migration applied successfully to the local database.
- Models and Database are in sync.
