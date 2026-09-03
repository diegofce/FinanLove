import uuid

import pytest

from app.application.auth import (
    AuthenticateUser,
    AuthenticationError,
    RegisterUser,
    RegisterUserCommand,
)
from app.domain.user import User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: list[User] = []

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((user for user in self.users if user.id == user_id), None)

    async def get_by_login(self, login: str) -> User | None:
        return next(
            (
                user
                for user in self.users
                if user.username == login or user.email == login
            ),
            None,
        )

    async def exists_by_login(self, username: str, email: str) -> bool:
        return any(
            user.username == username or user.email == email for user in self.users
        )

    async def add(self, user: User) -> User:
        self.users.append(user)
        return user


@pytest.mark.asyncio
async def test_register_hashes_password_and_authenticates() -> None:
    repository = InMemoryUserRepository()
    register = RegisterUser(repository)
    authenticate = AuthenticateUser(repository)

    user = await register.execute(
        RegisterUserCommand(
            username="diego",
            email="diego@example.com",
            first_name="Diego",
            last_name="User",
            password="correct horse battery staple",
        )
    )

    assert user.password_hash != "correct horse battery staple"
    authenticated_user = await authenticate.execute(
        "diego", "correct horse battery staple"
    )
    assert authenticated_user.id == user.id


@pytest.mark.asyncio
async def test_authentication_rejects_invalid_password() -> None:
    repository = InMemoryUserRepository()
    register = RegisterUser(repository)
    await register.execute(
        RegisterUserCommand(
            username="diego",
            email="diego@example.com",
            first_name="Diego",
            last_name="User",
            password="correct horse battery staple",
        )
    )

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        await AuthenticateUser(repository).execute("diego", "wrong password")
