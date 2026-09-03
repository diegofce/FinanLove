import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.account import AccountType
from app.domain.debt import DebtStatus
from app.domain.loan import LoanStatus, RepaymentStatus
from app.domain.transaction import TransactionType


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    role: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CreateAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: AccountType
    currency: str = Field(default="COP", min_length=3, max_length=3)
    current_balance: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    account_type: AccountType
    currency: str
    current_balance: Decimal
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreateTransactionRequest(BaseModel):
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    destination_account_id: uuid.UUID | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    description: str
    category: str | None
    destination_account_id: uuid.UUID | None
    occurred_at: datetime | None


class CreateLoanRequest(BaseModel):
    lender_id: uuid.UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    due_date: datetime | None = None


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    borrower_id: uuid.UUID
    lender_id: uuid.UUID
    amount: Decimal
    description: str
    status: LoanStatus
    due_date: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    lender_account_id: uuid.UUID | None = None
    borrower_account_id: uuid.UUID | None = None


class LoanStatusRequest(BaseModel):
    status: LoanStatus
    lender_account_id: uuid.UUID | None = None
    borrower_account_id: uuid.UUID | None = None


class CreateRepaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    source_account_id: uuid.UUID | None = None
    destination_account_id: uuid.UUID | None = None


class RepaymentStatusRequest(BaseModel):
    status: RepaymentStatus


class RepaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    loan_id: uuid.UUID
    amount: Decimal
    status: RepaymentStatus
    created_at: datetime | None
    updated_at: datetime | None


class CreateBudgetRequest(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    period_start: date
    period_end: date
    limit_amount: Decimal = Field(gt=0, decimal_places=2)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    category: str
    period_start: date
    period_end: date
    limit_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    percentage_used: Decimal


class CreateGoalRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_amount: Decimal = Field(gt=0, decimal_places=2)
    deadline: date | None = None


class ContributionRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    source_account_id: uuid.UUID | None = None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    target_amount: Decimal
    contributed_amount: Decimal
    deadline: date | None
    progress_percentage: Decimal


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    read_at: datetime | None


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str


class CreateRecurringTransactionRequest(BaseModel):
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    frequency: str = Field(min_length=1, max_length=20)
    next_run_at: datetime


class RecurringTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    description: str
    category: str | None
    frequency: str
    next_run_at: datetime
    is_active: bool


class CreateDebtRequest(BaseModel):
    creditor: str = Field(min_length=1, max_length=150)
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    due_date: date | None = None


class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    creditor: str
    amount: Decimal
    description: str
    due_date: date | None
    status: DebtStatus


class CreateInstallmentRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    due_date: date


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    debt_id: uuid.UUID
    amount: Decimal
    due_date: date
    status: DebtStatus


class DashboardResponse(BaseModel):
    total_balance: Decimal
    income: Decimal
    expenses: Decimal
    active_loans: int
    goals: int
