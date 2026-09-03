import uuid
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.account import Account, AccountType
from app.infrastructure.models.account import AccountModel


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, account: Account) -> Account:
        model = AccountModel(
            id=account.id,
            owner_id=account.owner_id,
            name=account.name,
            account_type=account.account_type.value,
            currency=account.currency,
            current_balance=account.current_balance,
            is_active=account.is_active,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]:
        result = await self.session.scalars(
            select(AccountModel)
            .where(AccountModel.owner_id == owner_id, AccountModel.is_active)
            .order_by(AccountModel.name)
        )
        return [self._to_domain(model) for model in result.all()]

    async def get_owned(
        self, account_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Account | None:
        model = await self.session.scalar(
            select(AccountModel).where(
                AccountModel.id == account_id,
                AccountModel.owner_id == owner_id,
                AccountModel.is_active,
            )
        )
        return self._to_domain(model) if model is not None else None

    async def update_balance(
        self, account_id: uuid.UUID, owner_id: uuid.UUID, delta: Decimal
    ) -> Account:
        result = await self.session.execute(
            update(AccountModel)
            .where(
                AccountModel.id == account_id,
                AccountModel.owner_id == owner_id,
                AccountModel.is_active,
                AccountModel.current_balance + delta >= 0,
            )
            .values(current_balance=AccountModel.current_balance + delta)
            .returning(AccountModel)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError("Insufficient account balance or account not found")
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            account_type=AccountType(model.account_type),
            currency=model.currency,
            current_balance=model.current_balance,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
