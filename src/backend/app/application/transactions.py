import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.application.ports import (
    AccountRepository,
    NotificationRepository,
    TransactionRepository,
)
from app.domain.planning import Notification
from app.domain.transaction import Transaction, TransactionType


@dataclass(frozen=True)
class CreateTransactionCommand:
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    description: str
    destination_account_id: uuid.UUID | None = None
    category: str | None = None


class CreateTransaction:
    def __init__(
        self,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        notifications: NotificationRepository | None = None,
    ) -> None:
        self.accounts = accounts
        self.transactions = transactions
        self.notifications = notifications

    async def execute(self, command: CreateTransactionCommand) -> Transaction:
        if command.amount <= 0:
            raise ValueError("Transaction amount must be positive")
        source = await self.accounts.get_owned(command.account_id, command.owner_id)
        if source is None:
            raise ValueError("Source account not found")
        if command.transaction_type is TransactionType.TRANSFER:
            if (
                command.destination_account_id is None
                or command.destination_account_id == command.account_id
            ):
                raise ValueError("Transfer requires a different destination account")
            destination = await self.accounts.get_owned(
                command.destination_account_id, command.owner_id
            )
            if destination is None:
                raise ValueError("Destination account not found")
            if source.currency != destination.currency:
                raise ValueError("Transfer accounts must use the same currency")
            if source.current_balance < command.amount:
                raise ValueError("Insufficient account balance")
            await self.accounts.update_balance(
                command.account_id, command.owner_id, -command.amount
            )
            await self.accounts.update_balance(
                command.destination_account_id, command.owner_id, command.amount
            )
        elif command.transaction_type is TransactionType.EXPENSE:
            if source.current_balance < command.amount:
                raise ValueError("Insufficient account balance")
            updated_account = await self.accounts.update_balance(
                command.account_id, command.owner_id, -command.amount
            )
            if self.notifications is not None and updated_account.current_balance == 0:
                await self.notifications.add(
                    Notification(
                        uuid.uuid4(),
                        command.owner_id,
                        "Saldo bajo",
                        f"La cuenta {updated_account.name} ha llegado a saldo cero.",
                    )
                )
        else:
            await self.accounts.update_balance(
                command.account_id, command.owner_id, command.amount
            )
        return await self.transactions.add(
            Transaction(
                id=uuid.uuid4(),
                owner_id=command.owner_id,
                account_id=command.account_id,
                transaction_type=command.transaction_type,
                amount=command.amount,
                description=command.description,
                category=command.category,
                destination_account_id=command.destination_account_id,
                occurred_at=datetime.now(UTC),
            )
        )


class ListUserTransactions:
    def __init__(self, transactions: TransactionRepository) -> None:
        self.transactions = transactions

    async def execute(self, owner_id: uuid.UUID) -> list[Transaction]:
        return await self.transactions.list_by_owner(owner_id)
