from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.infrastructure.models.base import Base
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

__all__ = ["Base", "engine", "SessionLocal", "get_db"]

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        async with SqlAlchemyUnitOfWork(session):
            yield session
