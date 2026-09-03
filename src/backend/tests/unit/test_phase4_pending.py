import uuid
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.application.planning import ContributeGoal, ContributeGoalCommand
from app.application.recurring import (
    CreateRecurringTransaction,
    CreateRecurringTransactionCommand,
)
from app.application.transactions import CreateTransaction, CreateTransactionCommand
from app.domain.account import Account, AccountType
from app.domain.planning import Notification, RecurringTransaction, SavingGoal
from app.domain.transaction import Transaction, TransactionType


class Goals:
    def __init__(self, goal: SavingGoal) -> None:
        self.goal = goal

    async def add(self, goal: SavingGoal) -> SavingGoal:
        return goal

    async def get_owned(
        self, goal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> SavingGoal | None:
        return (
            self.goal
            if self.goal.id == goal_id and self.goal.owner_id == owner_id
            else None
        )

    async def update(self, goal: SavingGoal) -> SavingGoal:
        self.goal = goal
        return goal


class Accounts:
    def __init__(self, account: Account) -> None:
        self.account = account

    async def add(self, account: Account) -> Account:
        return account

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]:
        return [self.account]

    async def get_owned(
        self, account_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Account | None:
        return (
            self.account
            if self.account.id == account_id and self.account.owner_id == owner_id
            else None
        )

    async def update_balance(
        self, account_id: uuid.UUID, owner_id: uuid.UUID, delta: Decimal
    ) -> Account:
        self.account = replace(
            self.account, current_balance=self.account.current_balance + delta
        )
        return self.account


class Transactions:
    def __init__(self) -> None:
        self.items: list[Transaction] = []

    async def add(self, transaction: Transaction) -> Transaction:
        self.items.append(transaction)
        return transaction

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Transaction]:
        return self.items


class Recurring:
    async def add(self, item: RecurringTransaction) -> RecurringTransaction:
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[RecurringTransaction]:
        return []


class Notifications:
    def __init__(self) -> None:
        self.items: list[Notification] = []

    async def add(self, notification: Notification) -> Notification:
        self.items.append(notification)
        return notification

    async def list_for_user(self, user_id: uuid.UUID) -> list[Notification]:
        return self.items

    async def get_owned(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        return None

    async def update(self, notification: Notification) -> Notification:
        return notification


@pytest.mark.asyncio
async def test_expense_to_zero_emits_low_balance_notification() -> None:
    owner_id = uuid.uuid4()
    source = Account(
        uuid.uuid4(), owner_id, "Cuenta", AccountType.BANK, "COP", Decimal("10.00")
    )
    notifications = Notifications()

    await CreateTransaction(Accounts(source), Transactions(), notifications).execute(
        CreateTransactionCommand(
            owner_id, source.id, TransactionType.EXPENSE, Decimal("10.00"), "Comida"
        )
    )

    assert len(notifications.items) == 1
    assert notifications.items[0].title == "Saldo bajo"


@pytest.mark.asyncio
async def test_goal_contribution_can_create_owned_expense() -> None:
    owner_id = uuid.uuid4()
    account = Account(
        uuid.uuid4(), owner_id, "Cuenta", AccountType.BANK, "COP", Decimal("100.00")
    )
    goal = SavingGoal(uuid.uuid4(), owner_id, "Reserva", Decimal("100.00"))
    transactions = Transactions()

    result = await ContributeGoal(Goals(goal), Accounts(account), transactions).execute(
        ContributeGoalCommand(goal.id, owner_id, Decimal("25.00"), account.id)
    )

    assert result.contributed_amount == Decimal("25.00")
    assert transactions.items[0].transaction_type is TransactionType.EXPENSE
    assert transactions.items[0].account_id == account.id


@pytest.mark.asyncio
async def test_recurring_transfer_is_rejected_without_execution_rules() -> None:
    with pytest.raises(ValueError, match="transfers"):
        await CreateRecurringTransaction(Recurring()).execute(
            CreateRecurringTransactionCommand(
                uuid.uuid4(),
                uuid.uuid4(),
                TransactionType.TRANSFER,
                Decimal("10.00"),
                "Ahorro",
                "monthly",
                datetime.now(UTC),
            )
        )
