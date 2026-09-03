from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.transactions import (
    CreateTransaction,
    CreateTransactionCommand,
    ListUserTransactions,
)
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.infrastructure.repositories.idempotency import IdempotencyRepository
from app.infrastructure.repositories.planning import SqlAlchemyNotificationRepository
from app.infrastructure.repositories.transactions import SqlAlchemyTransactionRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import CreateTransactionRequest, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    request: CreateTransactionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> TransactionResponse:
    idempotency = IdempotencyRepository(session)
    if idempotency_key:
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "transaction"
        )
        if existing_id:
            existing = await SqlAlchemyTransactionRepository(session).get_owned(
                existing_id, current_user.id
            )
            if existing is not None:
                return TransactionResponse.model_validate(existing)
    try:
        transaction = await CreateTransaction(
            SqlAlchemyAccountRepository(session),
            SqlAlchemyTransactionRepository(session),
            SqlAlchemyNotificationRepository(session),
        ).execute(
            CreateTransactionCommand(
                owner_id=current_user.id,
                account_id=request.account_id,
                transaction_type=request.transaction_type,
                amount=request.amount,
                description=request.description,
                category=request.category,
                destination_account_id=request.destination_account_id,
            )
        )
    except ValueError as error:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "transaction", transaction.id
            )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "transaction"
            )
            if existing_id:
                existing = await SqlAlchemyTransactionRepository(session).get_owned(
                    existing_id, current_user.id
                )
                if existing is not None:
                    return TransactionResponse.model_validate(existing)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return TransactionResponse.model_validate(transaction)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[TransactionResponse]:
    transactions = await ListUserTransactions(
        SqlAlchemyTransactionRepository(session)
    ).execute(current_user.id)
    return [TransactionResponse.model_validate(item) for item in transactions]
