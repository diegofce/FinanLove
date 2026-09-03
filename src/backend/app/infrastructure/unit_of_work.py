from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()


async def get_unit_of_work(
    session: AsyncSession,
) -> AsyncIterator[SqlAlchemyUnitOfWork]:
    async with SqlAlchemyUnitOfWork(session) as unit_of_work:
        yield unit_of_work
