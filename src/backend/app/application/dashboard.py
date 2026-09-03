import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.application.ports import (
    AccountListRepository,
    GoalListRepository,
    LoanListRepository,
    TransactionListRepository,
)
from app.domain.loan import LoanStatus
from app.domain.transaction import TransactionType


@dataclass(frozen=True)
class DashboardSummary:
    total_balance: Decimal
    income: Decimal
    expenses: Decimal
    active_loans: int
    goals: int


class GetDashboard:
    def __init__(
        self,
        accounts: AccountListRepository,
        transactions: TransactionListRepository,
        loans: LoanListRepository,
        goals: GoalListRepository,
    ) -> None:
        self.accounts = accounts
        self.transactions = transactions
        self.loans = loans
        self.goals = goals

    async def execute(self, owner_id: uuid.UUID) -> DashboardSummary:
        account_items = await self.accounts.list_by_owner(owner_id)
        transaction_items = await self.transactions.list_by_owner(owner_id)
        loan_items = await self.loans.list_for_user(owner_id)
        goal_items = await self.goals.list_by_owner(owner_id)
        return DashboardSummary(
            total_balance=sum(
                (item.current_balance for item in account_items), Decimal("0")
            ),
            income=sum(
                (
                    item.amount
                    for item in transaction_items
                    if item.transaction_type is TransactionType.INCOME
                ),
                Decimal("0"),
            ),
            expenses=sum(
                (
                    item.amount
                    for item in transaction_items
                    if item.transaction_type is TransactionType.EXPENSE
                ),
                Decimal("0"),
            ),
            active_loans=sum(
                item.status is LoanStatus.ACCEPTED for item in loan_items),
            goals=len(goal_items),
        )
