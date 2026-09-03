import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.transaction import Transaction, TransactionType
from app.infrastructure.models.transaction import TransactionModel


class SqlAlchemyTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, transaction: Transaction) -> Transaction:
        model = TransactionModel(
            id=transaction.id,
            owner_id=transaction.owner_id,
            account_id=transaction.account_id,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount,
            description=transaction.description,
            category=transaction.category,
            destination_account_id=transaction.destination_account_id,
            occurred_at=transaction.occurred_at,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_owned(
        self, transaction_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Transaction | None:
        model = await self.session.scalar(
            select(TransactionModel).where(
                TransactionModel.id == transaction_id,
                TransactionModel.owner_id == owner_id,
            )
        )
        return self._to_domain(model) if model else None

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Transaction]:
        result = await self.session.scalars(
            select(TransactionModel)
            .where(TransactionModel.owner_id == owner_id)
            .order_by(TransactionModel.occurred_at.desc())
        )
        return [self._to_domain(model) for model in result.all()]

    @staticmethod
    def _to_domain(model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            owner_id=model.owner_id,
            account_id=model.account_id,
            transaction_type=TransactionType(model.transaction_type),
            amount=model.amount,
            description=model.description,
            category=model.category,
            destination_account_id=model.destination_account_id,
            occurred_at=model.occurred_at,
        )
