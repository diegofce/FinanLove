import uuid
from decimal import Decimal
from typing import Protocol

from app.domain.account import Account
from app.domain.debt import Debt, Installment
from app.domain.loan import Loan, LoanRepayment
from app.domain.planning import (
    Budget,
    Category,
    Notification,
    RecurringTransaction,
    SavingGoal,
)
from app.domain.transaction import Transaction
from app.domain.user import User


class DebtRepository(Protocol):
    async def add(self, item: Debt) -> Debt: ...
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Debt]: ...

    async def get_owned(
        self, debt_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Debt | None: ...
    async def add_installment(self, item: Installment) -> Installment: ...
    async def list_installments(
        self, debt_id: uuid.UUID) -> list[Installment]: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def get_by_login(self, login: str) -> User | None: ...

    async def exists_by_login(self, username: str, email: str) -> bool: ...

    async def add(self, user: User) -> User: ...


class AccountRepository(Protocol):
    async def add(self, account: Account) -> Account: ...

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]: ...

    async def get_owned(
        self, account_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Account | None: ...

    async def update_balance(
        self, account_id: uuid.UUID, owner_id: uuid.UUID, delta: Decimal
    ) -> Account: ...


class AccountListRepository(Protocol):
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]: ...


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> Transaction: ...

    async def list_by_owner(
        self, owner_id: uuid.UUID) -> list[Transaction]: ...


class TransactionListRepository(Protocol):
    async def list_by_owner(
        self, owner_id: uuid.UUID) -> list[Transaction]: ...


class LoanRepository(Protocol):
    async def add(self, loan: Loan) -> Loan: ...

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]: ...

    async def get_for_user(
        self, loan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Loan | None: ...

    async def update(self, loan: Loan) -> Loan: ...

    async def accepted_repayment_total(
        self, loan_id: uuid.UUID) -> Decimal: ...

    async def add_repayment(
        self, repayment: LoanRepayment) -> LoanRepayment: ...

    async def get_repayment_for_loan(
        self, repayment_id: uuid.UUID, loan_id: uuid.UUID
    ) -> LoanRepayment | None: ...

    async def update_repayment(
        self, repayment: LoanRepayment) -> LoanRepayment: ...


class LoanDecisionRepository(Protocol):
    async def get_for_user(
        self, loan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Loan | None: ...

    async def update(self, loan: Loan) -> Loan: ...


class LoanCreationRepository(Protocol):
    async def add(self, loan: Loan) -> Loan: ...


class LoanListRepository(Protocol):
    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]: ...


class BudgetRepository(Protocol):
    async def add(self, item: Budget) -> Budget: ...
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Budget]: ...


class GoalRepository(Protocol):
    async def add(self, item: SavingGoal) -> SavingGoal: ...

    async def get_owned(
        self, goal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> SavingGoal | None: ...
    async def update(self, item: SavingGoal) -> SavingGoal: ...

    async def add_contribution(
        self, goal_id: uuid.UUID, owner_id: uuid.UUID, amount: Decimal
    ) -> SavingGoal: ...


class GoalListRepository(Protocol):
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[SavingGoal]: ...


class NotificationRepository(Protocol):
    async def add(self, item: Notification) -> Notification: ...

    async def list_for_user(
        self, user_id: uuid.UUID) -> list[Notification]: ...

    async def get_owned(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None: ...
    async def update(self, item: Notification) -> Notification: ...


class CategoryRepository(Protocol):
    async def add(self, category: Category) -> Category: ...
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Category]: ...


class RecurringTransactionRepository(Protocol):
    async def add(
        self, item: RecurringTransaction) -> RecurringTransaction: ...

    async def list_by_owner(
        self, owner_id: uuid.UUID
    ) -> list[RecurringTransaction]: ...
