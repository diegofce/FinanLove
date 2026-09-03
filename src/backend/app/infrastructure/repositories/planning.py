import uuid
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.planning import (
    Budget,
    Category,
    Notification,
    RecurringTransaction,
    SavingGoal,
)
from app.infrastructure.models.planning import (
    BudgetModel,
    CategoryModel,
    NotificationModel,
    RecurringTransactionModel,
    SavingGoalModel,
)
from app.infrastructure.models.transaction import TransactionModel


class SqlAlchemyBudgetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: Budget) -> Budget:
        model = BudgetModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Budget]:
        result = await self.session.scalars(
            select(BudgetModel).where(BudgetModel.owner_id == owner_id)
        )
        budgets: list[Budget] = []
        for model in result.all():
            spent = await self.session.scalar(
                select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
                    TransactionModel.owner_id == owner_id,
                    TransactionModel.category == model.category,
                    TransactionModel.transaction_type == "EXPENSE",
                    TransactionModel.occurred_at >= model.period_start,
                    TransactionModel.occurred_at <= model.period_end,
                )
            )
            budgets.append(
                Budget(**{**model.__dict__, "spent_amount": spent or 0}))
        return budgets


class SqlAlchemyGoalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: SavingGoal) -> SavingGoal:
        model = SavingGoalModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def get_owned(
        self, goal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> SavingGoal | None:
        model = await self.session.scalar(
            select(SavingGoalModel).where(
                SavingGoalModel.id == goal_id,
                SavingGoalModel.owner_id == owner_id,
            )
        )
        return SavingGoal(**model.__dict__) if model else None

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[SavingGoal]:
        result = await self.session.scalars(
            select(SavingGoalModel)
            .where(SavingGoalModel.owner_id == owner_id)
            .order_by(SavingGoalModel.name)
        )
        return [SavingGoal(**model.__dict__) for model in result.all()]

    async def update(self, item: SavingGoal) -> SavingGoal:
        model = await self.session.get(SavingGoalModel, item.id)
        if model is None:
            raise ValueError("Goal not found")
        model.contributed_amount = item.contributed_amount
        await self.session.flush()
        return item

    async def add_contribution(
        self, goal_id: uuid.UUID, owner_id: uuid.UUID, amount: Decimal
    ) -> SavingGoal:
        result = await self.session.execute(
            update(SavingGoalModel)
            .where(
                SavingGoalModel.id == goal_id,
                SavingGoalModel.owner_id == owner_id,
            )
            .values(
                contributed_amount=SavingGoalModel.contributed_amount + amount
            )
            .returning(SavingGoalModel)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Goal not found")
        return SavingGoal(**model.__dict__)


class SqlAlchemyNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: Notification) -> Notification:
        model = NotificationModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_for_user(self, user_id: uuid.UUID) -> list[Notification]:
        result = await self.session.scalars(
            select(NotificationModel).where(
                NotificationModel.user_id == user_id)
        )
        return [Notification(**model.__dict__) for model in result.all()]

    async def get_owned(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        model = await self.session.scalar(
            select(NotificationModel).where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
            )
        )
        return Notification(**model.__dict__) if model else None

    async def update(self, item: Notification) -> Notification:
        model = await self.session.get(NotificationModel, item.id)
        if model is None:
            raise ValueError("Notification not found")
        model.read_at = item.read_at
        await self.session.flush()
        return item


class SqlAlchemyCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: Category) -> Category:
        model = CategoryModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Category]:
        result = await self.session.scalars(
            select(CategoryModel)
            .where(CategoryModel.owner_id == owner_id)
            .order_by(CategoryModel.name)
        )
        return [Category(**model.__dict__) for model in result.all()]


class SqlAlchemyRecurringTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: RecurringTransaction) -> RecurringTransaction:
        model = RecurringTransactionModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[RecurringTransaction]:
        result = await self.session.scalars(
            select(RecurringTransactionModel).where(
                RecurringTransactionModel.owner_id == owner_id
            )
        )
        return [RecurringTransaction(**model.__dict__) for model in result.all()]
