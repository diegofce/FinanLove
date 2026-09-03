import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports import DebtRepository
from app.domain.debt import Debt, Installment


@dataclass(frozen=True)
class CreateDebtCommand:
    owner_id: uuid.UUID
    creditor: str
    amount: Decimal
    description: str
    due_date: date | None = None


class CreateDebt:
    def __init__(self, repository: DebtRepository) -> None:
        self.repository = repository

    async def execute(self, command: CreateDebtCommand) -> Debt:
        if command.amount <= 0:
            raise ValueError("Debt amount must be positive")
        if not command.creditor.strip() or not command.description.strip():
            raise ValueError("Creditor and description are required")
        return await self.repository.add(Debt(uuid.uuid4(), **command.__dict__))


@dataclass(frozen=True)
class CreateInstallmentCommand:
    debt_id: uuid.UUID
    amount: Decimal
    due_date: date


class CreateInstallment:
    def __init__(self, repository: DebtRepository) -> None:
        self.repository = repository

    async def execute(self, command: CreateInstallmentCommand) -> Installment:
        if command.amount <= 0:
            raise ValueError("Installment amount must be positive")
        return await self.repository.add_installment(
            Installment(uuid.uuid4(), **command.__dict__)
        )
