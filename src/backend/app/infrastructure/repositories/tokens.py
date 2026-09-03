import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.refresh_token import RefreshTokenModel


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _hash(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    async def issue(self, user_id: uuid.UUID, ttl_days: int = 30) -> str:
        raw = secrets.token_urlsafe(48)
        self.session.add(
            RefreshTokenModel(
                user_id=user_id,
                token_hash=self._hash(raw),
                expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
            )
        )
        await self.session.flush()
        return raw

    async def rotate(self, raw: str) -> tuple[uuid.UUID, str] | None:
        token = await self.session.scalar(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.token_hash == self._hash(raw),
                RefreshTokenModel.is_revoked.is_(False),
                RefreshTokenModel.expires_at > datetime.now(UTC),
            )
            .with_for_update()
        )
        if token is None:
            return None
        replacement = await self.issue(token.user_id)
        token.is_revoked = True
        token.revoked_at = datetime.now(UTC)
        return token.user_id, replacement

    async def revoke(self, raw: str) -> None:
        token = await self.session.scalar(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == self._hash(raw),
                RefreshTokenModel.is_revoked.is_(False),
            )
        )
        if token is not None:
            token.is_revoked = True
            token.revoked_at = datetime.now(UTC)
