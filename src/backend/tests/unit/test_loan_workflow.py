import uuid
from decimal import Decimal

import pytest

from app.application.loans import ChangeLoanStatus, ChangeLoanStatusCommand
from app.domain.loan import Loan, LoanStatus


class LoanRepositoryStub:
    def __init__(self, loan: Loan) -> None:
        self.loan = loan

    async def get_for_user(self, loan_id: uuid.UUID, user_id: uuid.UUID) -> Loan | None:
        if loan_id == self.loan.id and user_id in (
            self.loan.borrower_id,
            self.loan.lender_id,
        ):
            return self.loan
        return None

    async def get_for_user_for_update(
        self, loan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Loan | None:
        return await self.get_for_user(loan_id, user_id)

    async def update(self, loan: Loan) -> Loan:
        self.loan = loan
        return loan


@pytest.mark.asyncio
async def test_only_lender_can_accept_requested_loan() -> None:
    borrower_id, lender_id = uuid.uuid4(), uuid.uuid4()
    loan = Loan(uuid.uuid4(), borrower_id, lender_id,
                Decimal("100.00"), "Reserva")
    repository = LoanRepositoryStub(loan)

    with pytest.raises(ValueError, match="lender"):
        await ChangeLoanStatus(repository).execute(
            ChangeLoanStatusCommand(loan.id, borrower_id, LoanStatus.ACCEPTED)
        )

    with pytest.raises(ValueError, match="account integration"):
        await ChangeLoanStatus(repository).execute(
            ChangeLoanStatusCommand(loan.id, lender_id, LoanStatus.ACCEPTED)
        )
