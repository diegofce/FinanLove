import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, TimestampMixin


class AccountModel(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="COP")
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
