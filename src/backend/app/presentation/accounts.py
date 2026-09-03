from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts import (
    CreateAccount,
    CreateAccountCommand,
    ListUserAccounts,
)
from app.domain.account import AccountType
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import AccountResponse, CreateAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    account = await CreateAccount(SqlAlchemyAccountRepository(session)).execute(
        CreateAccountCommand(
            owner_id=current_user.id,
            name=request.name,
            account_type=AccountType(request.account_type),
            currency=request.currency,
            current_balance=request.current_balance,
        )
    )
    await session.commit()
    return AccountResponse.model_validate(account)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AccountResponse]:
    accounts = await ListUserAccounts(SqlAlchemyAccountRepository(session)).execute(
        current_user.id
    )
    return [AccountResponse.model_validate(account) for account in accounts]
