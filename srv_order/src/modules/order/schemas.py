from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PaginationSchema(BaseModel):
    offset: int = 0
    limit: int = 20


class OrderStatusUpdateSchema(BaseModel):
    id_order: int
    status: str


class PaymentStatusUpdateSchema(BaseModel):
    id_order: int
    payment_success: bool


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid_user: UUID
    status_order: str
    status_payment: bool
    created_at: datetime
    total_price: Decimal
    items: List[dict]
