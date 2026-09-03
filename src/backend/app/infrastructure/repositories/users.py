import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user import User
from app.infrastructure.models.user import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self.session.get(UserModel, user_id)
        return self._to_domain(model) if model else None

    async def get_by_login(self, login: str) -> User | None:
        statement = select(UserModel).where(
            or_(UserModel.username == login, UserModel.email == login)
        )
        model = await self.session.scalar(statement)
        return self._to_domain(model) if model else None

    async def exists_by_login(self, username: str, email: str) -> bool:
        statement = select(UserModel.id).where(
            or_(UserModel.username == username, UserModel.email == email)
        )
        return await self.session.scalar(statement) is not None

    async def add(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            role=user.role,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            password_hash=model.password_hash,
            is_active=model.is_active,
            role=model.role,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
