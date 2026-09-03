import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class Budget:
    id: uuid.UUID
    owner_id: uuid.UUID
    category: str
    period_start: date
    period_end: date
    limit_amount: Decimal
    spent_amount: Decimal = Decimal("0")

    @property
    def remaining_amount(self) -> Decimal:
        return self.limit_amount - self.spent_amount

    @property
    def percentage_used(self) -> Decimal:
        if self.limit_amount == 0:
            return Decimal("0")
        return (self.spent_amount / self.limit_amount * 100).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class SavingGoal:
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    target_amount: Decimal
    contributed_amount: Decimal = Decimal("0")
    deadline: date | None = None

    @property
    def progress_percentage(self) -> Decimal:
        if self.target_amount == 0:
            return Decimal("0")
        return min(
            Decimal("100"),
            (self.contributed_amount / self.target_amount * 100).quantize(
                Decimal("0.01")
            ),
        )


@dataclass(frozen=True)
class Notification:
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    read_at: datetime | None = None


@dataclass(frozen=True)
class Category:
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str


@dataclass(frozen=True)
class RecurringTransaction:
    id: uuid.UUID
    owner_id: uuid.UUID
    account_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    description: str
    frequency: str
    next_run_at: datetime
    category: str | None = None
    is_active: bool = True
