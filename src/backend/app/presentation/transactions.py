from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
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
from app.presentation.idempotency import request_fingerprint
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
    fingerprint = request_fingerprint(request.model_dump(mode="json"))
    if idempotency_key:
        existing_record = await idempotency.get_record(
            current_user.id, idempotency_key, "transaction"
        )
        if existing_record and existing_record.fingerprint != fingerprint:
            raise HTTPException(
                status_code=409, detail="Idempotency key payload conflict"
            )
        if existing_record:
            existing = await SqlAlchemyTransactionRepository(session).get_owned(
                existing_record.response_id, current_user.id
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
        if idempotency_key:
            inserted = await idempotency.add(
                current_user.id,
                idempotency_key,
                "transaction",
                transaction.id,
                fingerprint,
            )
            if not inserted:
                raise HTTPException(
                    status_code=409, detail="Idempotency key already used"
                )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
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
