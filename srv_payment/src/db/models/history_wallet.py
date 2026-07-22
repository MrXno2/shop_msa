from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import DateTime, Integer, Numeric, String, func, Enum as SAEnum
from srv_payment.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class TransactionType(str, Enum):
    PAYMENT = "payment"
    DEPOSITED = "deposited"


class HistoryWalletORM(Base):
    __tablename__ = "history_wallets"

    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        primary_key=True
    )
    transaction_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transactionstatus_enum"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    order_id: Mapped[int] = mapped_column(Integer, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)