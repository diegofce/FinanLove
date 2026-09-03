import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class LoanStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"


class RepaymentStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Loan:
    id: uuid.UUID
    borrower_id: uuid.UUID
    lender_id: uuid.UUID
    amount: Decimal
    description: str
    status: LoanStatus = LoanStatus.REQUESTED
    due_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    lender_account_id: uuid.UUID | None = None
    borrower_account_id: uuid.UUID | None = None


@dataclass(frozen=True)
class LoanRepayment:
    id: uuid.UUID
    loan_id: uuid.UUID
    amount: Decimal
    status: RepaymentStatus = RepaymentStatus.REQUESTED
    created_at: datetime | None = None
    updated_at: datetime | None = None
