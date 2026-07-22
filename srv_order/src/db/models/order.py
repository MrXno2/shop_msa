from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, DateTime, Enum as SAEnum, Float, Integer, Numeric, func
from srv_order.src.db.models.base import BaseUUID, Base
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemSchema(BaseModel):
    uuid_product: UUID
    name: str
    price: float = Field(ge=0)
    quantity: int = Field(ge=1, default=1)


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
    status_order: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING
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
