from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from sqlalchemy import DateTime, Integer, Numeric, String, func
from srv_payment.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


TransactionType = Literal["payment", "deposited"]


class HistoryWalletORM(Base):
    __tablename__ = "history_wallets"

    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True
    )
    uuid_user: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=False,
        index=True,
    )
    transaction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        String(20),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    order_id: Mapped[int] = mapped_column(Integer, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)