import uuid
from dataclasses import dataclass

from pwdlib import PasswordHash

from app.application.ports import UserRepository
from app.domain.user import User

password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class RegisterUserCommand:
    username: str
    email: str
    first_name: str
    last_name: str
    password: str


class AuthenticationError(ValueError):
    pass


class RegisterUser:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def execute(self, command: RegisterUserCommand) -> User:
        if await self.users.exists_by_login(command.username, command.email):
            raise AuthenticationError("Username or email is already registered")
        user = User(
            id=uuid.uuid4(),
            username=command.username,
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            password_hash=password_hash.hash(command.password),
            is_active=True,
        )
        return await self.users.add(user)


class AuthenticateUser:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def execute(self, login: str, password: str) -> User:
        user = await self.users.get_by_login(login)
        if user is None or not password_hash.verify(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Invalid credentials")
        return user
