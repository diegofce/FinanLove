import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


@dataclass(frozen=True)
class Transaction:
    id: uuid.UUID
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: TransactionType
    amount: Decimal
    description: str
    destination_account_id: uuid.UUID | None = None
    occurred_at: datetime | None = None
    created_at: datetime | None = None
    category: str | None = None
