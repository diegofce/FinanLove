import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class AccountType(StrEnum):
    BANK = "BANK"
    WALLET = "WALLET"
    CASH = "CASH"
    OTHER = "OTHER"


@dataclass(frozen=True)
class Account:
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    account_type: AccountType
    currency: str
    current_balance: Decimal
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
