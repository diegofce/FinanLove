import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.loan import Loan, LoanRepayment, LoanStatus, RepaymentStatus
from app.infrastructure.models.loan import LoanModel, LoanRepaymentModel


class SqlAlchemyLoanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, loan: Loan) -> Loan:
        model = LoanModel(
            id=loan.id,
            borrower_id=loan.borrower_id,
            lender_id=loan.lender_id,
            amount=loan.amount,
            description=loan.description,
            status=loan.status.value,
            due_date=loan.due_date,
            lender_account_id=loan.lender_account_id,
            borrower_account_id=loan.borrower_account_id,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]:
        result = await self.session.scalars(
            select(LoanModel)
            .where(
                or_(
                    LoanModel.borrower_id == user_id,
                    LoanModel.lender_id == user_id,
                )
            )
            .order_by(LoanModel.created_at.desc())
        )
        return [self._to_domain(model) for model in result.all()]

    async def get_for_user(self, loan_id: uuid.UUID, user_id: uuid.UUID) -> Loan | None:
        model = await self.session.scalar(
            select(LoanModel).where(
                LoanModel.id == loan_id,
                or_(LoanModel.borrower_id == user_id,
                    LoanModel.lender_id == user_id),
            )
        )
        return self._to_domain(model) if model else None

    async def get_for_user_for_update(
        self, loan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Loan | None:
        model = await self.session.scalar(
            select(LoanModel)
            .where(
                LoanModel.id == loan_id,
                or_(LoanModel.borrower_id == user_id,
                    LoanModel.lender_id == user_id),
            )
            .with_for_update()
        )
        return self._to_domain(model) if model else None

    async def update(self, loan: Loan) -> Loan:
        model = await self.session.get(LoanModel, loan.id)
        if model is None:
            raise ValueError("Loan not found")
        model.status = loan.status.value
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def accepted_repayment_total(self, loan_id: uuid.UUID) -> Decimal:
        total = await self.session.scalar(
            select(func.coalesce(func.sum(LoanRepaymentModel.amount), 0)).where(
                LoanRepaymentModel.loan_id == loan_id,
                LoanRepaymentModel.status == RepaymentStatus.ACCEPTED.value,
            )
        )
        return Decimal(str(total))

    async def add_repayment(self, repayment: LoanRepayment) -> LoanRepayment:
        model = LoanRepaymentModel(
            id=repayment.id,
            loan_id=repayment.loan_id,
            amount=repayment.amount,
            status=repayment.status.value,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_repayment_domain(model)

    async def get_repayment_for_loan(
        self, repayment_id: uuid.UUID, loan_id: uuid.UUID
    ) -> LoanRepayment | None:
        model = await self.session.scalar(
            select(LoanRepaymentModel).where(
                LoanRepaymentModel.id == repayment_id,
                LoanRepaymentModel.loan_id == loan_id,
            )
        )
        return self._to_repayment_domain(model) if model else None

    async def get_repayment_for_loan_for_update(
        self, repayment_id: uuid.UUID, loan_id: uuid.UUID
    ) -> LoanRepayment | None:
        model = await self.session.scalar(
            select(LoanRepaymentModel)
            .where(
                LoanRepaymentModel.id == repayment_id,
                LoanRepaymentModel.loan_id == loan_id,
            )
            .with_for_update()
        )
        return self._to_repayment_domain(model) if model else None

    async def update_repayment(self, repayment: LoanRepayment) -> LoanRepayment:
        model = await self.session.get(LoanRepaymentModel, repayment.id)
        if model is None:
            raise ValueError("Repayment not found")
        model.status = repayment.status.value
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_repayment_domain(model)

    @staticmethod
    def _to_domain(model: LoanModel) -> Loan:
        return Loan(
            id=model.id,
            borrower_id=model.borrower_id,
            lender_id=model.lender_id,
            amount=model.amount,
            description=model.description,
            status=LoanStatus(model.status),
            due_date=model.due_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            lender_account_id=model.lender_account_id,
            borrower_account_id=model.borrower_account_id,
        )

    @staticmethod
    def _to_repayment_domain(model: LoanRepaymentModel) -> LoanRepayment:
        return LoanRepayment(
            id=model.id,
            loan_id=model.loan_id,
            amount=model.amount,
            status=RepaymentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
