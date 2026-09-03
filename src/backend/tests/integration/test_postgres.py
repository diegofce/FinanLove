import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.mark.asyncio
async def test_postgres_is_available_for_integration_tests(
    postgres_engine: AsyncEngine,
) -> None:
    async with postgres_engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
