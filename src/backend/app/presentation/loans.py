import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.loans import (
    ChangeLoanStatus,
    ChangeLoanStatusCommand,
    ChangeRepaymentStatus,
    ChangeRepaymentStatusCommand,
    ListUserLoans,
    RequestLoan,
    RequestLoanCommand,
    RequestRepayment,
    RequestRepaymentCommand,
)
from app.domain.user import User
from app.infrastructure.database import get_db
from app.infrastructure.repositories.accounts import SqlAlchemyAccountRepository
from app.infrastructure.repositories.idempotency import IdempotencyRepository
from app.infrastructure.repositories.loans import SqlAlchemyLoanRepository
from app.infrastructure.repositories.planning import SqlAlchemyNotificationRepository
from app.infrastructure.repositories.transactions import SqlAlchemyTransactionRepository
from app.infrastructure.repositories.users import SqlAlchemyUserRepository
from app.presentation.dependencies import get_current_user
from app.presentation.idempotency import request_fingerprint
from app.presentation.schemas import (
    CreateLoanRequest,
    CreateRepaymentRequest,
    LoanResponse,
    LoanStatusRequest,
    RepaymentResponse,
    RepaymentStatusRequest,
)

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def request_loan(
    request: CreateLoanRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> LoanResponse:
    idempotency = IdempotencyRepository(session)
    fingerprint = request_fingerprint(request.model_dump(mode="json"))
    if idempotency_key:
        record = await idempotency.get_record(
            current_user.id, idempotency_key, "loan_request"
        )
        if record and record.fingerprint != fingerprint:
            raise HTTPException(
                status_code=409, detail="Idempotency key payload conflict"
            )
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "loan_request"
        )
        if existing_id:
            existing = await SqlAlchemyLoanRepository(session).get_for_user(
                existing_id, current_user.id
            )
            if existing is not None:
                return LoanResponse.model_validate(existing)
    try:
        loan = await RequestLoan(
            SqlAlchemyUserRepository(session),
            SqlAlchemyLoanRepository(session),
            SqlAlchemyNotificationRepository(session),
        ).execute(
            RequestLoanCommand(
                borrower_id=current_user.id,
                lender_id=request.lender_id,
                amount=request.amount,
                description=request.description,
                due_date=request.due_date,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "loan_request", loan.id,
                fingerprint
            )
    except IntegrityError:
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "loan_request"
            )
            if existing_id:
                existing = await SqlAlchemyLoanRepository(session).get_for_user(
                    existing_id, current_user.id
                )
                if existing is not None:
                    return LoanResponse.model_validate(existing)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return LoanResponse.model_validate(loan)


@router.get("", response_model=list[LoanResponse])
async def list_loans(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[LoanResponse]:
    loans = await ListUserLoans(SqlAlchemyLoanRepository(session)).execute(
        current_user.id
    )
    return [LoanResponse.model_validate(item) for item in loans]


@router.patch("/{loan_id}/status", response_model=LoanResponse)
async def change_loan_status(
    loan_id: uuid.UUID,
    request: LoanStatusRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> LoanResponse:
    idempotency = IdempotencyRepository(session)
    fingerprint = request_fingerprint(request.model_dump(mode="json"))
    if idempotency_key:
        record = await idempotency.get_record(
            current_user.id, idempotency_key, "loan_acceptance"
        )
        if record and record.fingerprint != fingerprint:
            raise HTTPException(
                status_code=409, detail="Idempotency key payload conflict"
            )
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "loan_acceptance"
        )
        if existing_id:
            existing = await SqlAlchemyLoanRepository(session).get_for_user(
                existing_id, current_user.id
            )
            if existing is not None:
                return LoanResponse.model_validate(existing)
    try:
        loan = await ChangeLoanStatus(
            SqlAlchemyLoanRepository(session),
            SqlAlchemyNotificationRepository(session),
            SqlAlchemyAccountRepository(session),
            SqlAlchemyTransactionRepository(session),
        ).execute(
            ChangeLoanStatusCommand(
                loan_id,
                current_user.id,
                request.status,
                request.lender_account_id,
                request.borrower_account_id,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "loan_acceptance", loan.id,
                fingerprint
            )
    except IntegrityError:
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "loan_acceptance"
            )
            if existing_id:
                existing = await SqlAlchemyLoanRepository(session).get_for_user(
                    existing_id, current_user.id
                )
                if existing is not None:
                    return LoanResponse.model_validate(existing)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return LoanResponse.model_validate(loan)


@router.post("/{loan_id}/repayments", response_model=RepaymentResponse, status_code=201)
async def request_repayment(
    loan_id: uuid.UUID,
    request: CreateRepaymentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> RepaymentResponse:
    idempotency = IdempotencyRepository(session)
    fingerprint = request_fingerprint(request.model_dump(mode="json"))
    if idempotency_key:
        record = await idempotency.get_record(
            current_user.id, idempotency_key, "repayment_request"
        )
        if record and record.fingerprint != fingerprint:
            raise HTTPException(
                status_code=409, detail="Idempotency key payload conflict"
            )
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "repayment_request"
        )
        if existing_id:
            existing = await SqlAlchemyLoanRepository(session).get_repayment_for_loan(
                existing_id, loan_id
            )
            if existing is not None:
                return RepaymentResponse.model_validate(existing)
    try:
        repayment = await RequestRepayment(SqlAlchemyLoanRepository(session)).execute(
            RequestRepaymentCommand(
                loan_id,
                current_user.id,
                request.amount,
                request.source_account_id,
                request.destination_account_id,
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "repayment_request", repayment.id,
                fingerprint
            )
    except IntegrityError:
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "repayment_request"
            )
            if existing_id:
                existing = await SqlAlchemyLoanRepository(
                    session
                ).get_repayment_for_loan(existing_id, loan_id)
                if existing is not None:
                    return RepaymentResponse.model_validate(existing)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return RepaymentResponse.model_validate(repayment)


@router.patch(
    "/{loan_id}/repayments/{repayment_id}/status",
    response_model=RepaymentResponse,
)
async def change_repayment_status(
    loan_id: uuid.UUID,
    repayment_id: uuid.UUID,
    request: RepaymentStatusRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> RepaymentResponse:
    idempotency = IdempotencyRepository(session)
    fingerprint = request_fingerprint(request.model_dump(mode="json"))
    if idempotency_key:
        record = await idempotency.get_record(
            current_user.id, idempotency_key, "repayment_acceptance"
        )
        if record and record.fingerprint != fingerprint:
            raise HTTPException(
                status_code=409, detail="Idempotency key payload conflict"
            )
        existing_id = await idempotency.get(
            current_user.id, idempotency_key, "repayment_acceptance"
        )
        if existing_id:
            existing = await SqlAlchemyLoanRepository(session).get_repayment_for_loan(
                existing_id, loan_id
            )
            if existing is not None:
                return RepaymentResponse.model_validate(existing)
    try:
        repayment = await ChangeRepaymentStatus(
            SqlAlchemyLoanRepository(session),
            SqlAlchemyAccountRepository(session),
            SqlAlchemyTransactionRepository(session),
        ).execute(
            ChangeRepaymentStatusCommand(
                loan_id, repayment_id, current_user.id, request.status
            )
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    try:
        if idempotency_key:
            await idempotency.add(
                current_user.id, idempotency_key, "repayment_acceptance", repayment.id,
                fingerprint
            )
    except IntegrityError:
        if idempotency_key:
            existing_id = await idempotency.get(
                current_user.id, idempotency_key, "repayment_acceptance"
            )
            if existing_id:
                existing = await SqlAlchemyLoanRepository(
                    session
                ).get_repayment_for_loan(existing_id, loan_id)
                if existing is not None:
                    return RepaymentResponse.model_validate(existing)
        raise HTTPException(
            status_code=409, detail="Idempotency key already used"
        ) from None
    return RepaymentResponse.model_validate(repayment)
