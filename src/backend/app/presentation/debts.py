import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.debts import (
    CreateDebt,
    CreateDebtCommand,
    CreateInstallment,
    CreateInstallmentCommand,
)
from app.application.ports import DebtRepository
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.debts import SqlAlchemyDebtRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import (
    CreateDebtRequest,
    CreateInstallmentRequest,
    DebtResponse,
    InstallmentResponse,
)

router = APIRouter(prefix="/debts", tags=["debts"])


def repository(session: AsyncSession) -> DebtRepository:
    return SqlAlchemyDebtRepository(session)


@router.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
async def create_debt(
    request: CreateDebtRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DebtResponse:
    try:
        item = await CreateDebt(repository(session)).execute(
            CreateDebtCommand(current_user.id, **request.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return DebtResponse.model_validate(item)


@router.get("", response_model=list[DebtResponse])
async def list_debts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[DebtResponse]:
    items = await repository(session).list_by_owner(current_user.id)
    return [DebtResponse.model_validate(item) for item in items]


@router.post(
    "/{debt_id}/installments",
    response_model=InstallmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_installment(
    debt_id: uuid.UUID,
    request: CreateInstallmentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> InstallmentResponse:
    repo = repository(session)
    if await repo.get_owned(debt_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Debt not found")
    try:
        item = await CreateInstallment(repo).execute(
            CreateInstallmentCommand(debt_id, **request.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return InstallmentResponse.model_validate(item)


@router.get("/{debt_id}/installments", response_model=list[InstallmentResponse])
async def list_installments(
    debt_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[InstallmentResponse]:
    repo = repository(session)
    if await repo.get_owned(debt_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Debt not found")
    items = await repo.list_installments(debt_id)
    return [InstallmentResponse.model_validate(item) for item in items]
