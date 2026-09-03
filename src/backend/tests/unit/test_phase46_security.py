import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pytest
from fastapi import HTTPException

from app.application.ports import AccountRepository as AccountRepositoryPort
from app.application.recurring import (
    CreateRecurringTransaction,
    CreateRecurringTransactionCommand,
)
from app.core.config import Settings
from app.domain.account import Account
from app.domain.planning import RecurringTransaction
from app.domain.transaction import TransactionType
from app.presentation.auth import _validate_csrf_origin


def test_refresh_requires_allowed_origin() -> None:
    with pytest.raises(HTTPException) as error:
        _validate_csrf_origin("https://attacker.example", None)
    assert error.value.status_code == 403


def test_refresh_accepts_allowed_referer() -> None:
    _validate_csrf_origin(None, "http://localhost:5173/account")


def test_production_rejects_weak_jwt_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET"):
        Settings.model_validate(
            {"APP_ENV": "production", "JWT_SECRET": "short"})


def test_production_accepts_strong_jwt_secret() -> None:
    Settings.model_validate({"APP_ENV": "production", "JWT_SECRET": "a" * 32})


class RecurringRepository:
    async def add(self, item: RecurringTransaction) -> RecurringTransaction:
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[RecurringTransaction]:
        return []


class AccountRepository:
    def __init__(self, account: Account | None) -> None:
        self.account = account

    async def get_owned(
        self, account_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Account | None:
        return self.account

    async def add(self, account: Account) -> Account:
        return account

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]:
        return []

    async def update_balance(
        self, account_id: uuid.UUID, owner_id: uuid.UUID, delta: Decimal
    ) -> Account:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_recurring_requires_an_active_owned_account() -> None:
    owner_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Account not found"):
        await CreateRecurringTransaction(
            RecurringRepository(), cast(AccountRepositoryPort, AccountRepository(None))
        ).execute(
            CreateRecurringTransactionCommand(
                owner_id,
                uuid.uuid4(),
                TransactionType.EXPENSE,
                Decimal("10.00"),
                "Rent",
                "monthly",
                datetime.now(UTC),
            )
        )
