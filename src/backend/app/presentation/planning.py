import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.categories import (
    CreateCategory,
    CreateCategoryCommand,
    ListCategories,
)
from app.application.planning import (
    ContributeGoal,
    ContributeGoalCommand,
    CreateBudget,
    CreateBudgetCommand,
    CreateGoal,
    CreateGoalCommand,
    ListBudgets,
    ListGoals,
    ListNotifications,
    MarkNotificationRead,
)
from app.application.recurring import (
    CreateRecurringTransaction,
    CreateRecurringTransactionCommand,
    ListRecurringTransactions,
)
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.infrastructure.repositories.idempotency import IdempotencyRepository
from app.infrastructure.repositories.planning import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyGoalRepository,
    SqlAlchemyNotificationRepository,
    SqlAlchemyRecurringTransactionRepository,
)
from app.infrastructure.repositories.transactions import SqlAlchemyTransactionRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import (
    BudgetResponse,
    CategoryResponse,
    ContributionRequest,
    CreateBudgetRequest,
    CreateCategoryRequest,
    CreateGoalRequest,
    CreateRecurringTransactionRequest,
    GoalResponse,
    NotificationResponse,
    RecurringTransactionResponse,
)

router = APIRouter(tags=["planning"])


@router.post(
    "/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED
)
async def create_budget(
    request: CreateBudgetRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetResponse:
    try:
        item = await CreateBudget(SqlAlchemyBudgetRepository(session)).execute(
            CreateBudgetCommand(current_user.id, **request.model_dump())
        )
    except ValueError as error:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error
    await session.commit()
    return BudgetResponse.model_validate(item, from_attributes=True)


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[BudgetResponse]:
    items = await ListBudgets(
        SqlAlchemyBudgetRepository(session), SqlAlchemyNotificationRepository(session)
    ).execute(current_user.id)
    return [BudgetResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: CreateGoalRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> GoalResponse:
    try:
        item = await CreateGoal(SqlAlchemyGoalRepository(session)).execute(
            CreateGoalCommand(current_user.id, **request.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    await session.commit()
    return GoalResponse.model_validate(item, from_attributes=True)


@router.get("/goals", response_model=list[GoalResponse])
async def list_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[GoalResponse]:
    items = await ListGoals(SqlAlchemyGoalRepository(session)).execute(current_user.id)
    return [GoalResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("/goals/{goal_id}/contributions", response_model=GoalResponse)
async def contribute_goal(
    goal_id: uuid.UUID,
    request: ContributionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> GoalResponse:
    idempotency = IdempotencyRepository(session)
    if idempotency_key:
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "goal_contribution"
        )
        if existing_id:
            existing = await SqlAlchemyGoalRepository(session).get_owned(
                existing_id, current_user.id
            )
            if existing is not None:
                return GoalResponse.model_validate(existing, from_attributes=True)
    try:
        item = await ContributeGoal(
            SqlAlchemyGoalRepository(session),
            SqlAlchemyAccountRepository(session),
            SqlAlchemyTransactionRepository(session),
        ).execute(
            ContributeGoalCommand(
                goal_id, current_user.id, request.amount, request.source_account_id
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "goal_contribution", item.id
            )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "goal_contribution"
            )
            if existing_id:
                existing = await SqlAlchemyGoalRepository(session).get_owned(
                    existing_id, current_user.id
                )
                if existing is not None:
                    return GoalResponse.model_validate(existing, from_attributes=True)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return GoalResponse.model_validate(item, from_attributes=True)


@router.get("/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[NotificationResponse]:
    items = await ListNotifications(SqlAlchemyNotificationRepository(session)).execute(
        current_user.id
    )
    return [
        NotificationResponse.model_validate(item, from_attributes=True)
        for item in items
    ]


@router.patch(
    "/notifications/{notification_id}/read", response_model=NotificationResponse
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationResponse:
    try:
        item = await MarkNotificationRead(
            SqlAlchemyNotificationRepository(session)
        ).execute(notification_id, current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    await session.commit()
    return NotificationResponse.model_validate(item, from_attributes=True)


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    request: CreateCategoryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    item = await CreateCategory(SqlAlchemyCategoryRepository(session)).execute(
        CreateCategoryCommand(current_user.id, request.name)
    )
    await session.commit()
    return CategoryResponse.model_validate(item, from_attributes=True)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryResponse]:
    items = await ListCategories(SqlAlchemyCategoryRepository(session)).execute(
        current_user.id
    )
    return [
        CategoryResponse.model_validate(item, from_attributes=True) for item in items
    ]


@router.post(
    "/recurring-transactions",
    response_model=RecurringTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recurring_transaction(
    request: CreateRecurringTransactionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RecurringTransactionResponse:
    try:
        item = await CreateRecurringTransaction(
            SqlAlchemyRecurringTransactionRepository(session),
            SqlAlchemyAccountRepository(session),
        ).execute(
            CreateRecurringTransactionCommand(current_user.id, **request.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    await session.commit()
    return RecurringTransactionResponse.model_validate(item, from_attributes=True)


@router.get(
    "/recurring-transactions", response_model=list[RecurringTransactionResponse]
)
async def list_recurring_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[RecurringTransactionResponse]:
    items = await ListRecurringTransactions(
        SqlAlchemyRecurringTransactionRepository(session)
    ).execute(current_user.id)
    return [
        RecurringTransactionResponse.model_validate(item, from_attributes=True)
        for item in items
    ]
