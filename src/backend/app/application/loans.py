import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.application.ports import (
    AccountRepository,
    LoanCreationRepository,
    LoanDecisionRepository,
    LoanRepository,
    NotificationRepository,
    TransactionRepository,
    UserRepository,
)
from app.domain.loan import Loan, LoanRepayment, LoanStatus, RepaymentStatus
from app.domain.planning import Notification
from app.domain.transaction import Transaction, TransactionType


@dataclass(frozen=True)
class RequestLoanCommand:
    borrower_id: uuid.UUID
    lender_id: uuid.UUID
    amount: Decimal
    description: str
    due_date: datetime | None = None


class RequestLoan:
    def __init__(
        self,
        users: UserRepository,
        loans: LoanCreationRepository,
        notifications: NotificationRepository | None = None,
    ) -> None:
        self.users = users
        self.loans = loans
        self.notifications = notifications

    async def execute(self, command: RequestLoanCommand) -> Loan:
        if command.amount <= 0:
            raise ValueError("Loan amount must be positive")
        if command.borrower_id == command.lender_id:
            raise ValueError("A loan requires two different users")
        lender = await self.users.get_by_id(command.lender_id)
        if lender is None or not lender.is_active:
            raise ValueError("Lender not found")
        loan = await self.loans.add(
            Loan(
                id=uuid.uuid4(),
                borrower_id=command.borrower_id,
                lender_id=command.lender_id,
                amount=command.amount,
                description=command.description,
                due_date=command.due_date,
            )
        )
        if self.notifications is not None:
            await self.notifications.add(
                Notification(
                    uuid.uuid4(),
                    command.lender_id,
                    "Nueva solicitud de préstamo",
                    f"{command.description}: {command.amount}",
                )
            )
        return loan


class ListUserLoans:
    def __init__(self, loans: LoanRepository) -> None:
        self.loans = loans

    async def execute(self, user_id: uuid.UUID) -> list[Loan]:
        return await self.loans.list_for_user(user_id)


@dataclass(frozen=True)
class ChangeLoanStatusCommand:
    loan_id: uuid.UUID
    user_id: uuid.UUID
    status: LoanStatus
    lender_account_id: uuid.UUID | None = None
    borrower_account_id: uuid.UUID | None = None


class ChangeLoanStatus:
    def __init__(
        self,
        loans: LoanDecisionRepository,
        notifications: NotificationRepository | None = None,
        accounts: AccountRepository | None = None,
        transactions: TransactionRepository | None = None,
    ) -> None:
        self.loans = loans
        self.notifications = notifications
        self.accounts = accounts
        self.transactions = transactions

    async def execute(self, command: ChangeLoanStatusCommand) -> Loan:
        loan = await self.loans.get_for_user_for_update(
            command.loan_id, command.user_id
        )
        if loan is None:
            raise ValueError("Loan not found")
        if command.user_id != loan.lender_id or loan.status is not LoanStatus.REQUESTED:
            raise ValueError("Only the lender can decide a requested loan")
        if command.status not in (LoanStatus.ACCEPTED, LoanStatus.REJECTED):
            raise ValueError("Invalid loan transition")
        if command.status is LoanStatus.ACCEPTED:
            if self.accounts is None or self.transactions is None:
                raise ValueError("Loan account integration is unavailable")
            if (
                command.lender_account_id is None or command.borrower_account_id is None
            ):
                raise ValueError("Accepted loan requires both account ids")
            lender_account = await self.accounts.get_owned(
                command.lender_account_id, loan.lender_id
            )
            borrower_account = await self.accounts.get_owned(
                command.borrower_account_id, loan.borrower_id
            )
            if lender_account is None or borrower_account is None:
                raise ValueError("Loan account not found")
            if lender_account.currency != borrower_account.currency:
                raise ValueError("Loan accounts must use the same currency")
            await self.accounts.update_balance(
                lender_account.id, loan.lender_id, -loan.amount
            )
            await self.accounts.update_balance(
                borrower_account.id, loan.borrower_id, loan.amount
            )
            await self.transactions.add(
                Transaction(
                    uuid.uuid4(),
                    loan.lender_id,
                    lender_account.id,
                    TransactionType.EXPENSE,
                    loan.amount,
                    f"Préstamo a {loan.borrower_id}",
                    destination_account_id=borrower_account.id,
                )
            )
            await self.transactions.add(
                Transaction(
                    uuid.uuid4(),
                    loan.borrower_id,
                    borrower_account.id,
                    TransactionType.INCOME,
                    loan.amount,
                    f"Préstamo de {loan.lender_id}",
                    destination_account_id=lender_account.id,
                )
            )
        updated = await self.loans.update(
            Loan(
                **{
                    **loan.__dict__,
                    "status": command.status,
                    "lender_account_id": command.lender_account_id
                    or loan.lender_account_id,
                    "borrower_account_id": command.borrower_account_id
                    or loan.borrower_account_id,
                }
            )
        )
        if self.notifications is not None:
            await self.notifications.add(
                Notification(
                    uuid.uuid4(),
                    loan.borrower_id,
                    "Estado de préstamo actualizado",
                    f"La solicitud '{loan.description}' ahora está "
                    f"{command.status.value}.",
                )
            )
        return updated


@dataclass(frozen=True)
class RequestRepaymentCommand:
    loan_id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    source_account_id: uuid.UUID | None = None
    destination_account_id: uuid.UUID | None = None


class RequestRepayment:
    def __init__(self, loans: LoanRepository) -> None:
        self.loans = loans

    async def execute(self, command: RequestRepaymentCommand) -> LoanRepayment:
        if command.amount <= 0:
            raise ValueError("Repayment amount must be positive")
        loan = await self.loans.get_for_user_for_update(
            command.loan_id, command.user_id
        )
        if loan is None or loan.borrower_id != command.user_id:
            raise ValueError("Only the borrower can request a repayment")
        accepted = await self.loans.accepted_repayment_total(loan.id)
        if loan.status is LoanStatus.SETTLED and accepted >= loan.amount:
            raise ValueError("Repayment exceeds outstanding loan amount")
        if loan.status is not LoanStatus.ACCEPTED:
            raise ValueError("Loan is not active")
        if accepted + command.amount > loan.amount:
            raise ValueError("Repayment exceeds outstanding loan amount")
        return await self.loans.add_repayment(
            LoanRepayment(uuid.uuid4(), loan.id, command.amount)
        )


@dataclass(frozen=True)
class ChangeRepaymentStatusCommand:
    loan_id: uuid.UUID
    repayment_id: uuid.UUID
    user_id: uuid.UUID
    status: RepaymentStatus


class ChangeRepaymentStatus:
    def __init__(
        self,
        loans: LoanRepository,
        accounts: AccountRepository | None = None,
        transactions: TransactionRepository | None = None,
    ) -> None:
        self.loans = loans
        self.accounts = accounts
        self.transactions = transactions

    async def execute(self, command: ChangeRepaymentStatusCommand) -> LoanRepayment:
        loan = await self.loans.get_for_user(command.loan_id, command.user_id)
        repayment = await self.loans.get_repayment_for_loan_for_update(
            command.repayment_id, command.loan_id
        )
        if loan is None or repayment is None:
            raise ValueError("Repayment not found")
        if (
            command.user_id != loan.lender_id
            or repayment.status is not RepaymentStatus.REQUESTED
        ):
            raise ValueError(
                "Only the lender can decide a requested repayment")
        if command.status not in (RepaymentStatus.ACCEPTED, RepaymentStatus.REJECTED):
            raise ValueError("Invalid repayment transition")
        if command.status is RepaymentStatus.ACCEPTED:
            if self.accounts is None or self.transactions is None:
                raise ValueError("Loan account integration is unavailable")
            if loan.borrower_account_id is None or loan.lender_account_id is None:
                raise ValueError("Loan accounts are not configured")
            source = await self.accounts.get_owned(
                loan.borrower_account_id, loan.borrower_id
            )
            destination = await self.accounts.get_owned(
                loan.lender_account_id, loan.lender_id
            )
            if source is None or destination is None:
                raise ValueError("Loan account not found")
            if source.currency != destination.currency:
                raise ValueError("Loan accounts must use the same currency")
            await self.accounts.update_balance(
                source.id, loan.borrower_id, -repayment.amount
            )
            await self.accounts.update_balance(
                destination.id, loan.lender_id, repayment.amount
            )
            await self.transactions.add(
                Transaction(
                    uuid.uuid4(),
                    loan.borrower_id,
                    source.id,
                    TransactionType.EXPENSE,
                    repayment.amount,
                    f"Devolución de préstamo {loan.id}",
                    destination_account_id=destination.id,
                )
            )
            await self.transactions.add(
                Transaction(
                    uuid.uuid4(),
                    loan.lender_id,
                    destination.id,
                    TransactionType.INCOME,
                    repayment.amount,
                    f"Devolución de préstamo {loan.id}",
                    destination_account_id=source.id,
                )
            )
        updated = await self.loans.update_repayment(
            LoanRepayment(**{**repayment.__dict__, "status": command.status})
        )
        if command.status is RepaymentStatus.ACCEPTED:
            total = await self.loans.accepted_repayment_total(loan.id)
            if total == loan.amount:
                await self.loans.update(
                    Loan(**{**loan.__dict__, "status": LoanStatus.SETTLED})
                )
        return updated
