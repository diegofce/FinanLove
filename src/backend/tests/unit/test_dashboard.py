import uuid
from decimal import Decimal

import pytest

from app.application.dashboard import GetDashboard
from app.domain.account import Account, AccountType
from app.domain.loan import Loan, LoanStatus
from app.domain.planning import SavingGoal
from app.domain.transaction import Transaction, TransactionType


class Accounts:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]:
        return [
            Account(
                uuid.uuid4(),
                owner_id,
                "Cuenta",
                AccountType.BANK,
                "COP",
                Decimal("100"),
            )
        ]


class Transactions:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Transaction]:
        return [
            Transaction(
                uuid.uuid4(),
                owner_id,
                uuid.uuid4(),
                TransactionType.INCOME,
                Decimal("50"),
                "Ingreso",
            )
        ]


class Loans:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]:
        return [
            Loan(
                uuid.uuid4(),
                user_id,
                uuid.uuid4(),
                Decimal("20"),
                "Préstamo",
                LoanStatus.ACCEPTED,
            )
        ]


class Goals:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[SavingGoal]:
        return [SavingGoal(uuid.uuid4(), owner_id, "Meta", Decimal("100"))]


@pytest.mark.asyncio
async def test_dashboard_aggregates_owned_financial_data() -> None:
    owner_id = uuid.uuid4()
    result = await GetDashboard(
        Accounts(owner_id), Transactions(
            owner_id), Loans(owner_id), Goals(owner_id)
    ).execute(owner_id)
    assert result.total_balance == Decimal("100")
    assert result.income == Decimal("50")
    assert result.expenses == Decimal("0")
    assert result.active_loans == 1
    assert result.goals == 1
