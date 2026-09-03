import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    password_hash: str
    is_active: bool
    role: str = "USER"
    created_at: datetime | None = None
    updated_at: datetime | None = None
