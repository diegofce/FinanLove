import uuid
from dataclasses import replace
from decimal import Decimal

import pytest

from app.application.loans import RequestLoan, RequestLoanCommand
from app.application.transactions import CreateTransaction, CreateTransactionCommand
from app.domain.account import Account, AccountType
from app.domain.loan import Loan
from app.domain.transaction import Transaction, TransactionType
from app.domain.user import User


class InMemoryAccounts:
    def __init__(self, accounts: list[Account]) -> None:
        self.accounts = accounts

    async def add(self, account: Account) -> Account:
        self.accounts.append(account)
        return account

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Account]:
        return [item for item in self.accounts if item.owner_id == owner_id]

    async def get_owned(
        self, account_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Account | None:
        return next(
            (
                item
                for item in self.accounts
                if item.id == account_id and item.owner_id == owner_id
            ),
            None,
        )

    async def update_balance(
        self, account_id: uuid.UUID, owner_id: uuid.UUID, delta: Decimal
    ) -> Account:
        account = await self.get_owned(account_id, owner_id)
        assert account is not None
        updated = replace(account, current_balance=account.current_balance + delta)
        self.accounts[self.accounts.index(account)] = updated
        return updated


class InMemoryTransactions:
    def __init__(self) -> None:
        self.items: list[Transaction] = []

    async def add(self, transaction: Transaction) -> Transaction:
        self.items.append(transaction)
        return transaction

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Transaction]:
        return [item for item in self.items if item.owner_id == owner_id]


class InMemoryUsers:
    def __init__(self, user_ids: set[uuid.UUID]) -> None:
        self.user_ids = user_ids

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        if user_id not in self.user_ids:
            return None
        return User(
            user_id, "lender", "lender@example.com", "Lender", "User", "hash", True
        )

    async def get_by_login(self, login: str) -> User | None:
        return None

    async def exists_by_login(self, username: str, email: str) -> bool:
        return False

    async def add(self, user: User) -> User:
        return user


class InMemoryLoans:
    def __init__(self) -> None:
        self.items: list[Loan] = []

    async def add(self, loan: Loan) -> Loan:
        self.items.append(loan)
        return loan

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]:
        return [
            item
            for item in self.items
            if item.borrower_id == user_id or item.lender_id == user_id
        ]


def account(owner_id: uuid.UUID, balance: str = "100.00") -> Account:
    return Account(
        uuid.uuid4(), owner_id, "Cuenta", AccountType.BANK, "COP", Decimal(balance)
    )


@pytest.mark.asyncio
async def test_expense_reduces_balance_and_persists_transaction() -> None:
    owner_id = uuid.uuid4()
    source = account(owner_id)
    accounts = InMemoryAccounts([source])
    transactions = InMemoryTransactions()

    await CreateTransaction(accounts, transactions).execute(
        CreateTransactionCommand(
            owner_id,
            source.id,
            TransactionType.EXPENSE,
            Decimal("25.50"),
            "Comida",
        )
    )

    assert accounts.accounts[0].current_balance == Decimal("74.50")
    assert transactions.items[0].transaction_type is TransactionType.EXPENSE


@pytest.mark.asyncio
async def test_expense_rejects_insufficient_balance() -> None:
    owner_id = uuid.uuid4()
    source = account(owner_id, "10.00")

    with pytest.raises(ValueError, match="Insufficient"):
        await CreateTransaction(
            InMemoryAccounts([source]), InMemoryTransactions()
        ).execute(
            CreateTransactionCommand(
                owner_id,
                source.id,
                TransactionType.EXPENSE,
                Decimal("10.01"),
                "Comida",
            )
        )


@pytest.mark.asyncio
async def test_transfer_requires_owned_same_currency_accounts() -> None:
    owner_id = uuid.uuid4()
    source = account(owner_id)
    destination = replace(account(owner_id), currency="USD")

    with pytest.raises(ValueError, match="same currency"):
        await CreateTransaction(
            InMemoryAccounts([source, destination]), InMemoryTransactions()
        ).execute(
            CreateTransactionCommand(
                owner_id,
                source.id,
                TransactionType.TRANSFER,
                Decimal("10.00"),
                "Ahorro",
                destination.id,
            )
        )


@pytest.mark.asyncio
async def test_loan_requires_active_different_lender() -> None:
    borrower_id = uuid.uuid4()
    lender_id = uuid.uuid4()
    loans = InMemoryLoans()
    loan = await RequestLoan(InMemoryUsers({lender_id}), loans).execute(
        RequestLoanCommand(borrower_id, lender_id, Decimal("50.00"), "Préstamo")
    )
    assert loan.status.value == "REQUESTED"

    with pytest.raises(ValueError, match="different users"):
        await RequestLoan(InMemoryUsers({borrower_id}), loans).execute(
            RequestLoanCommand(borrower_id, borrower_id, Decimal("50.00"), "Préstamo")
        )
