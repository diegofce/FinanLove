import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.database import get_db
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.main import app

BACKEND_ROOT = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
        if os.getenv("CI") == "true":
            pytest.fail("CI requires TEST_DATABASE_URL PostgreSQL")
        pytest.skip("TEST_DATABASE_URL PostgreSQL is not configured")
    return database_url


@pytest_asyncio.fixture(scope="session")
async def postgres_engine(test_database_url: str) -> AsyncIterator[AsyncEngine]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = test_database_url
    environment["TEST_DATABASE_URL"] = test_database_url
    await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
    )
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    async with engine.connect() as connection:
        await connection.run_sync(lambda sync_connection: None)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(postgres_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def http_client(
    postgres_engine: AsyncEngine,
) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def database_override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            async with SqlAlchemyUnitOfWork(session):
                yield session

    app.dependency_overrides[get_db] = database_override
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
