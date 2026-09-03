import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.debt import Debt, DebtStatus, Installment
from app.infrastructure.models.debt import DebtModel, InstallmentModel


class SqlAlchemyDebtRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, item: Debt) -> Debt:
        model = DebtModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Debt]:
        result = await self.session.scalars(
            select(DebtModel).where(DebtModel.owner_id == owner_id)
        )
        return [self._debt(model) for model in result.all()]

    async def get_owned(self, debt_id: uuid.UUID, owner_id: uuid.UUID) -> Debt | None:
        model = await self.session.scalar(
            select(DebtModel).where(
                DebtModel.id == debt_id, DebtModel.owner_id == owner_id
            )
        )
        return self._debt(model) if model else None

    async def add_installment(self, item: Installment) -> Installment:
        model = InstallmentModel(**item.__dict__)
        self.session.add(model)
        await self.session.flush()
        return item

    async def list_installments(self, debt_id: uuid.UUID) -> list[Installment]:
        result = await self.session.scalars(
            select(InstallmentModel).where(InstallmentModel.debt_id == debt_id)
        )
        return [self._installment(model) for model in result.all()]

    @staticmethod
    def _debt(model: DebtModel) -> Debt:
        return Debt(**{**model.__dict__, "status": DebtStatus(model.status)})

    @staticmethod
    def _installment(model: InstallmentModel) -> Installment:
        return Installment(**{**model.__dict__, "status": DebtStatus(model.status)})
