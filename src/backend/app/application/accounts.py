import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.application.ports import AccountRepository
from app.domain.account import Account, AccountType


@dataclass(frozen=True)
class CreateAccountCommand:
    owner_id: uuid.UUID
    name: str
    account_type: AccountType
    currency: str = "COP"
    current_balance: Decimal = Decimal("0.00")


class CreateAccount:
    def __init__(self, accounts: AccountRepository) -> None:
        self.accounts = accounts

    async def execute(self, command: CreateAccountCommand) -> Account:
        if command.current_balance < 0:
            raise ValueError("Account balance cannot be negative")
        account = Account(
            id=uuid.uuid4(),
            owner_id=command.owner_id,
            name=command.name,
            account_type=command.account_type,
            currency=command.currency,
            current_balance=command.current_balance,
        )
        return await self.accounts.add(account)


class ListUserAccounts:
    def __init__(self, accounts: AccountRepository) -> None:
        self.accounts = accounts

    async def execute(self, owner_id: uuid.UUID) -> list[Account]:
        return await self.accounts.list_by_owner(owner_id)
