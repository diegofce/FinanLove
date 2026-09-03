import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.idempotency import IdempotencyKeyModel


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_record(
        self, owner_id: uuid.UUID, key: str, operation: str
    ) -> IdempotencyKeyModel | None:
        lock_key = f"{owner_id}:{operation}:{key}"
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": lock_key},
        )
        item = await self.session.scalar(
            select(IdempotencyKeyModel).where(
                IdempotencyKeyModel.owner_id == owner_id,
                IdempotencyKeyModel.key == key,
                IdempotencyKeyModel.operation == operation,
            )
        )
        return item

    async def get(
        self, owner_id: uuid.UUID, key: str, operation: str
    ) -> uuid.UUID | None:
        item = await self.get_record(owner_id, key, operation)
        return item.response_id if item else None

    async def add(
        self,
        owner_id: uuid.UUID,
        key: str,
        operation: str,
        response_id: uuid.UUID,
        fingerprint: str,
    ) -> bool:
        statement = insert(IdempotencyKeyModel).values(
            owner_id=owner_id,
            key=key,
            operation=operation,
            response_id=response_id,
            fingerprint=fingerprint,
            created_at=datetime.now(UTC),
        )
        result = await self.session.execute(
            statement.on_conflict_do_nothing(
                index_elements=["owner_id", "key", "operation"]
            )
        )
        await self.session.flush()
        return bool(getattr(result, "rowcount", 0) == 1)
