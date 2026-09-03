import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.application.ports import AccountRepository, RecurringTransactionRepository
from app.domain.planning import RecurringTransaction
from app.domain.transaction import TransactionType


@dataclass(frozen=True)
class CreateRecurringTransactionCommand:
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    description: str
    frequency: str
    next_run_at: datetime
    category: str | None = None


class CreateRecurringTransaction:
    def __init__(
        self,
        repository: RecurringTransactionRepository,
        accounts: AccountRepository | None = None,
    ) -> None:
        self.repository = repository
        self.accounts = accounts

    async def execute(
        self, command: CreateRecurringTransactionCommand
    ) -> RecurringTransaction:
        if command.amount <= 0:
            raise ValueError("Recurring amount must be positive")
        if command.transaction_type is TransactionType.TRANSFER:
            raise ValueError("Recurring transfers are not supported")
        if not command.frequency.strip():
            raise ValueError("Frequency is required")
        if (
            self.accounts is None
            or await self.accounts.get_owned(command.account_id, command.owner_id)
            is None
        ):
            raise ValueError("Account not found")
        return await self.repository.add(
            RecurringTransaction(
                uuid.uuid4(),
                command.owner_id,
                command.account_id,
                command.transaction_type.value,
                command.amount,
                command.description,
                command.frequency,
                command.next_run_at,
                command.category,
            )
        )


class ListRecurringTransactions:
    def __init__(self, repository: RecurringTransactionRepository) -> None:
        self.repository = repository

    async def execute(self, owner_id: uuid.UUID) -> list[RecurringTransaction]:
        return await self.repository.list_by_owner(owner_id)
