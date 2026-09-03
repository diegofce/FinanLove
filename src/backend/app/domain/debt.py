import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class DebtStatus(StrEnum):
    OPEN = "OPEN"
    SETTLED = "SETTLED"


@dataclass(frozen=True)
class Debt:
    id: uuid.UUID
    owner_id: uuid.UUID
    creditor: str
    amount: Decimal
    description: str
    due_date: date | None = None
    status: DebtStatus = DebtStatus.OPEN


@dataclass(frozen=True)
class Installment:
    id: uuid.UUID
    debt_id: uuid.UUID
    amount: Decimal
    due_date: date
    status: DebtStatus = DebtStatus.OPEN
