import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.idempotency import IdempotencyKeyModel


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self, owner_id: uuid.UUID, key: str, operation: str
    ) -> uuid.UUID | None:
        item = await self.session.scalar(
            select(IdempotencyKeyModel).where(
                IdempotencyKeyModel.owner_id == owner_id,
                IdempotencyKeyModel.key == key,
                IdempotencyKeyModel.operation == operation,
            )
        )
        return item.response_id if item else None

    async def add(
        self, owner_id: uuid.UUID, key: str, operation: str, response_id: uuid.UUID
    ) -> None:
        self.session.add(
            IdempotencyKeyModel(
                owner_id=owner_id,
                key=key,
                operation=operation,
                response_id=response_id,
                created_at=datetime.now(UTC),
            )
        )
        await self.session.flush()
