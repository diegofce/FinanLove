import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.auth import RegisterUser, RegisterUserCommand
from app.application.loans import (
    ChangeLoanStatus,
    ChangeLoanStatusCommand,
    ChangeRepaymentStatus,
    ChangeRepaymentStatusCommand,
    RequestLoan,
    RequestLoanCommand,
    RequestRepayment,
    RequestRepaymentCommand,
)
from app.application.transactions import CreateTransaction, CreateTransactionCommand
from app.domain.account import Account, AccountType
from app.domain.loan import LoanStatus, RepaymentStatus
from app.domain.transaction import TransactionType
from app.infrastructure.models.account import AccountModel
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.infrastructure.repositories.loans import SqlAlchemyLoanRepository
from app.infrastructure.repositories.planning import SqlAlchemyNotificationRepository
from app.infrastructure.repositories.transactions import SqlAlchemyTransactionRepository
from app.infrastructure.repositories.users import SqlAlchemyUserRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


async def create_user_and_account(
    session: AsyncSession, balance: Decimal = Decimal("100.00")
) -> tuple[uuid.UUID, uuid.UUID]:
    user = await RegisterUser(SqlAlchemyUserRepository(session)).execute(
        RegisterUserCommand(
            username=f"integration_{uuid.uuid4().hex[:12]}",
            email=f"{uuid.uuid4().hex}@example.com",
            first_name="Integration",
            last_name="Tester",
            password="A-very-secure-password-123",
        )
    )
    account = await SqlAlchemyAccountRepository(session).add(
        Account(
            id=uuid.uuid4(),
            owner_id=user.id,
            name="Concurrent account",
            account_type=AccountType.BANK,
            currency="COP",
            current_balance=balance,
        )
    )
    return user.id, account.id


async def execute_expense(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    description: str,
) -> bool:
    async with session_factory() as session:
        try:
            async with SqlAlchemyUnitOfWork(session):
                await CreateTransaction(
                    SqlAlchemyAccountRepository(session),
                    SqlAlchemyTransactionRepository(session),
                    SqlAlchemyNotificationRepository(session),
                ).execute(
                    CreateTransactionCommand(
                        owner_id=user_id,
                        account_id=account_id,
                        transaction_type=TransactionType.EXPENSE,
                        amount=Decimal("80.00"),
                        description=description,
                    )
                )
            return True
        except ValueError:
            return False


async def execute_transfer(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    source_id: uuid.UUID,
    destination_id: uuid.UUID,
) -> bool:
    async with session_factory() as session:
        try:
            async with SqlAlchemyUnitOfWork(session):
                await CreateTransaction(
                    SqlAlchemyAccountRepository(session),
                    SqlAlchemyTransactionRepository(session),
                ).execute(
                    CreateTransactionCommand(
                        owner_id=user_id,
                        account_id=source_id,
                        transaction_type=TransactionType.TRANSFER,
                        amount=Decimal("80.00"),
                        description="concurrent transfer",
                        destination_account_id=destination_id,
                    )
                )
            return True
        except ValueError:
            return False


@pytest.mark.asyncio
async def test_schema_has_alembic_revision_and_financial_tables(
    postgres_engine: AsyncEngine,
) -> None:
    async with postgres_engine.connect() as connection:
        revision = await connection.scalar(
            text("SELECT version_num FROM alembic_version")
        )
        tables = await connection.execute(
            text(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = 'public'"
            )
        )
        table_names = {row[0] for row in tables}
    assert revision == "0010_add_idempotency_fingerprint"
    assert {"users", "accounts", "transactions",
            "idempotency_keys"} <= table_names


@pytest.mark.asyncio
async def test_concurrent_expenses_allow_only_one_and_leave_20(
    postgres_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False)
    async with session_factory() as setup_session:
        async with SqlAlchemyUnitOfWork(setup_session):
            user_id, account_id = await create_user_and_account(setup_session)

    results = await asyncio.gather(
        execute_expense(session_factory, user_id, account_id, "expense A"),
        execute_expense(session_factory, user_id, account_id, "expense B"),
    )

    async with session_factory() as verification_session:
        balance = await verification_session.scalar(
            select(AccountModel.current_balance).where(
                AccountModel.id == account_id)
        )
        transactions = await verification_session.scalar(
            select(func.count()).select_from(text("transactions")).where(
                text("account_id = :account_id")
            ).params(account_id=account_id)
        )
    assert sorted(results) == [False, True]
    assert balance == Decimal("20.00")
    assert transactions == 1


@pytest.mark.asyncio
async def test_concurrent_transfers_allow_only_one_and_preserve_both_balances(
    postgres_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False)
    async with session_factory() as setup_session:
        async with SqlAlchemyUnitOfWork(setup_session):
            user_id, source_id = await create_user_and_account(
                setup_session, Decimal("100.00")
            )
            destination = await SqlAlchemyAccountRepository(setup_session).add(
                Account(
                    uuid.uuid4(),
                    user_id,
                    "Transfer destination",
                    AccountType.BANK,
                    "COP",
                    Decimal("0.00"),
                )
            )
            destination_id = destination.id

    results = await asyncio.gather(
        execute_transfer(session_factory, user_id, source_id, destination_id),
        execute_transfer(session_factory, user_id, source_id, destination_id),
    )

    async with session_factory() as verification_session:
        balances = await verification_session.scalars(
            select(AccountModel.current_balance)
            .where(AccountModel.id.in_([source_id, destination_id]))
            .order_by(AccountModel.id)
        )
        transaction_count = await verification_session.scalar(
            select(func.count()).select_from(text("transactions")).where(
                text("account_id = :account_id")
            ).params(account_id=source_id)
        )
    assert sorted(results) == [False, True]
    assert sorted(balances.all()) == [Decimal("20.00"), Decimal("80.00")]
    assert transaction_count == 1


@pytest.mark.asyncio
async def test_loan_repayments_track_partial_full_excess_and_rollback(
    postgres_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False)
    async with session_factory() as setup_session:
        async with SqlAlchemyUnitOfWork(setup_session):
            borrower_id, borrower_account_id = await create_user_and_account(
                setup_session, Decimal("100.00")
            )
            lender_id, lender_account_id = await create_user_and_account(
                setup_session, Decimal("200.00")
            )
            loan = await RequestLoan(
                SqlAlchemyUserRepository(setup_session),
                SqlAlchemyLoanRepository(setup_session),
            ).execute(
                RequestLoanCommand(
                    borrower_id, lender_id, Decimal("100.00"), "Test loan"
                )
            )
            loan = await ChangeLoanStatus(
                SqlAlchemyLoanRepository(setup_session),
                accounts=SqlAlchemyAccountRepository(setup_session),
                transactions=SqlAlchemyTransactionRepository(setup_session),
            ).execute(
                ChangeLoanStatusCommand(
                    loan.id,
                    lender_id,
                    LoanStatus.ACCEPTED,
                    lender_account_id,
                    borrower_account_id,
                )
            )
            assert loan.status is LoanStatus.ACCEPTED

            loans = SqlAlchemyLoanRepository(setup_session)
            repayment = await RequestRepayment(loans).execute(
                RequestRepaymentCommand(
                    loan.id, borrower_id, Decimal("30.00"),
                    borrower_account_id, lender_account_id,
                )
            )
            repayment = await ChangeRepaymentStatus(
                loans,
                SqlAlchemyAccountRepository(setup_session),
                SqlAlchemyTransactionRepository(setup_session),
            ).execute(
                ChangeRepaymentStatusCommand(
                    loan.id, repayment.id, lender_id, RepaymentStatus.ACCEPTED
                )
            )
            assert repayment.status is RepaymentStatus.ACCEPTED
            current_loan = await loans.get_for_user(loan.id, lender_id)
            assert current_loan is not None
            assert current_loan.status is LoanStatus.ACCEPTED

            final_repayment = await RequestRepayment(loans).execute(
                RequestRepaymentCommand(
                    loan.id, borrower_id, Decimal("70.00"),
                    borrower_account_id, lender_account_id,
                )
            )
            await ChangeRepaymentStatus(
                loans,
                SqlAlchemyAccountRepository(setup_session),
                SqlAlchemyTransactionRepository(setup_session),
            ).execute(
                ChangeRepaymentStatusCommand(
                    loan.id, final_repayment.id, lender_id, RepaymentStatus.ACCEPTED
                )
            )
            current_loan = await loans.get_for_user(loan.id, lender_id)
            assert current_loan is not None
            assert current_loan.status is LoanStatus.SETTLED
            with pytest.raises(ValueError, match="exceeds"):
                await RequestRepayment(loans).execute(
                    RequestRepaymentCommand(
                        loan.id, borrower_id, Decimal("1.00"),
                        borrower_account_id, lender_account_id,
                    )
                )

    async with session_factory() as verification_session:
        loan_status = await verification_session.scalar(
            select(LoanModel.status).where(LoanModel.id == loan.id)
        )
        assert loan_status == LoanStatus.SETTLED.value


@pytest.mark.asyncio
async def test_transfer_failure_rolls_back_both_account_balances(
    postgres_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False)
    async with session_factory() as session:
        async with SqlAlchemyUnitOfWork(session):
            user_id, source_id = await create_user_and_account(
                session, Decimal("100.00")
            )
            destination = await SqlAlchemyAccountRepository(session).add(
                Account(
                    uuid.uuid4(),
                    user_id,
                    "Destination",
                    AccountType.BANK,
                    "COP",
                    Decimal("50.00"),
                )
            )
            destination_id = destination.id
    async with session_factory() as session:
        with pytest.raises(ValueError, match="Insufficient"):
            async with SqlAlchemyUnitOfWork(session):
                await CreateTransaction(
                    SqlAlchemyAccountRepository(session),
                    SqlAlchemyTransactionRepository(session),
                ).execute(
                    CreateTransactionCommand(
                        user_id,
                        source_id,
                        TransactionType.TRANSFER,
                        Decimal("120.00"),
                        "too much",
                        destination_id,
                    )
                )
    async with session_factory() as session:
        balances = await session.scalars(
            select(AccountModel.current_balance)
            .where(AccountModel.id.in_([source_id, destination_id]))
            .order_by(AccountModel.id)
        )
        assert sorted(balances.all()) == [Decimal("50.00"), Decimal("100.00")]


@pytest.mark.asyncio
async def test_multi_entity_balance_changes_rollback_together(
    postgres_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(
        postgres_engine, expire_on_commit=False)
    async with session_factory() as setup_session:
        async with SqlAlchemyUnitOfWork(setup_session):
            user_id, source_id = await create_user_and_account(
                setup_session, Decimal("100.00")
            )
            destination = await SqlAlchemyAccountRepository(setup_session).add(
                Account(
                    uuid.uuid4(),
                    user_id,
                    "Rollback destination",
                    AccountType.BANK,
                    "COP",
                    Decimal("50.00"),
                )
            )
            destination_id = destination.id

    async with session_factory() as session:
        with pytest.raises(RuntimeError, match="force rollback"):
            async with SqlAlchemyUnitOfWork(session):
                repository = SqlAlchemyAccountRepository(session)
                await repository.update_balance(source_id, user_id, Decimal("-10.00"))
                await repository.update_balance(
                    destination_id, user_id, Decimal("10.00")
                )
                raise RuntimeError("force rollback")

    async with session_factory() as session:
        balances = await session.scalars(
            select(AccountModel.current_balance)
            .where(AccountModel.id.in_([source_id, destination_id]))
            .order_by(AccountModel.id)
        )
        assert sorted(balances.all()) == [Decimal("50.00"), Decimal("100.00")]
