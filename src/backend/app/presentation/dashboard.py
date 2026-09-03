from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard import GetDashboard
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.infrastructure.repositories.loans import SqlAlchemyLoanRepository
from app.infrastructure.repositories.planning import SqlAlchemyGoalRepository
from app.infrastructure.repositories.transactions import SqlAlchemyTransactionRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardResponse:
    result = await GetDashboard(
        SqlAlchemyAccountRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyLoanRepository(session),
        SqlAlchemyGoalRepository(session),
    ).execute(current_user.id)
    return DashboardResponse.model_validate(result)
