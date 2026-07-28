from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from srv_payment.src.db.models.base import Base


class WalletORM(Base):
    __tablename__ = "wallets_users"

    uuid_user: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=False,
        index=True,
        primary_key=True,
    )
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
