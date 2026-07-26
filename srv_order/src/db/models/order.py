from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, DateTime, Enum as SAEnum, Integer, Numeric, func
from srv_order.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from core_app.enums import OrderStatusEnum


class OrderORM(Base):
    __tablename__ = "orders_users"

    id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,  # автоинкремент
        index=True,
        primary_key=True
    )
    uuid_user: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=False,
        index=True
    )
    status_order: Mapped[OrderStatusEnum] = mapped_column(
        SAEnum(OrderStatusEnum, name="order_status_enum"),
        nullable=False,
        default=OrderStatusEnum.PENDING
    )
    status_payment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    items: Mapped[List[dict]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )
