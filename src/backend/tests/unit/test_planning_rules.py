import uuid
from datetime import date
from decimal import Decimal

from app.domain.planning import Budget, SavingGoal


def test_budget_reports_spent_remaining_and_percentage() -> None:
    budget = Budget(
        uuid.uuid4(),
        uuid.uuid4(),
        "Comida",
        date(2026, 9, 1),
        date(2026, 9, 30),
        Decimal("400.00"),
        Decimal("125.50"),
    )
    assert budget.remaining_amount == Decimal("274.50")
    assert budget.percentage_used == Decimal("31.38")


def test_goal_caps_progress_at_one_hundred_percent() -> None:
    goal = SavingGoal(
        uuid.uuid4(), uuid.uuid4(), "Reserva", Decimal("100.00"), Decimal("120.00")
    )
    assert goal.progress_percentage == Decimal("100.00")
