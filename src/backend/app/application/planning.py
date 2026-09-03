import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from app.application.ports import (
    AccountRepository,
    BudgetRepository,
    GoalListRepository,
    GoalRepository,
    NotificationRepository,
    TransactionRepository,
)
from app.domain.planning import Budget, Notification, SavingGoal
from app.domain.transaction import Transaction, TransactionType


@dataclass(frozen=True)
class CreateBudgetCommand:
    owner_id: uuid.UUID
    category: str
    period_start: date
    period_end: date
    limit_amount: Decimal


class CreateBudget:
    def __init__(self, repository: BudgetRepository) -> None:
        self.repository = repository

    async def execute(self, command: CreateBudgetCommand) -> Budget:
        if command.limit_amount <= 0 or command.period_end < command.period_start:
            raise ValueError("Invalid budget")
        return await self.repository.add(Budget(uuid.uuid4(), **command.__dict__))


class ListBudgets:
    def __init__(
        self,
        repository: BudgetRepository,
        notifications: NotificationRepository | None = None,
    ) -> None:
        self.repository = repository
        self.notifications = notifications

    async def execute(self, owner_id: uuid.UUID) -> list[Budget]:
        budgets = await self.repository.list_by_owner(owner_id)
        if self.notifications is not None:
            for budget in budgets:
                if budget.spent_amount > budget.limit_amount:
                    await self.notifications.add(
                        Notification(
                            uuid.uuid4(),
                            owner_id,
                            "Presupuesto excedido",
                            f"El presupuesto de {budget.category} ha sido excedido.",
                        )
                    )
        return budgets


@dataclass(frozen=True)
class CreateGoalCommand:
    owner_id: uuid.UUID
    name: str
    target_amount: Decimal
    deadline: date | None = None


class CreateGoal:
    def __init__(self, repository: GoalRepository) -> None:
        self.repository = repository

    async def execute(self, command: CreateGoalCommand) -> SavingGoal:
        if command.target_amount <= 0:
            raise ValueError("Goal target must be positive")
        return await self.repository.add(SavingGoal(uuid.uuid4(), **command.__dict__))


class ListGoals:
    def __init__(self, repository: GoalListRepository) -> None:
        self.repository = repository

    async def execute(self, owner_id: uuid.UUID) -> list[SavingGoal]:
        return await self.repository.list_by_owner(owner_id)


@dataclass(frozen=True)
class ContributeGoalCommand:
    goal_id: uuid.UUID
    owner_id: uuid.UUID
    amount: Decimal
    source_account_id: uuid.UUID | None = None


class ContributeGoal:
    def __init__(
        self,
        repository: GoalRepository,
        accounts: AccountRepository | None = None,
        transactions: TransactionRepository | None = None,
    ) -> None:
        self.repository = repository
        self.accounts = accounts
        self.transactions = transactions

    async def execute(self, command: ContributeGoalCommand) -> SavingGoal:
        if command.amount <= 0:
            raise ValueError("Contribution must be positive")
        goal = await self.repository.get_owned(command.goal_id, command.owner_id)
        if goal is None:
            raise ValueError("Goal not found")
        if command.source_account_id is not None:
            if self.accounts is None or self.transactions is None:
                raise ValueError("Goal movement integration is unavailable")
            account = await self.accounts.get_owned(
                command.source_account_id, command.owner_id
            )
            if account is None:
                raise ValueError("Source account not found")
            if account.current_balance < command.amount:
                raise ValueError("Insufficient account balance")
            await self.accounts.update_balance(
                account.id, command.owner_id, -command.amount
            )
            await self.transactions.add(
                Transaction(
                    uuid.uuid4(),
                    command.owner_id,
                    account.id,
                    TransactionType.EXPENSE,
                    command.amount,
                    f"Contribución a meta: {goal.name}",
                    category="Ahorro",
                )
            )
        return await self.repository.add_contribution(
            goal.id, command.owner_id, command.amount
        )


class ListNotifications:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def execute(self, user_id: uuid.UUID) -> list[Notification]:
        return await self.repository.list_for_user(user_id)


class MarkNotificationRead:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def execute(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification:
        notification = await self.repository.get_owned(notification_id, user_id)
        if notification is None:
            raise ValueError("Notification not found")
        return await self.repository.update(
            Notification(
                **{
                    **notification.__dict__,
                    "read_at": notification.read_at or datetime.now(UTC),
                }
            )
        )
