from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CartCacheProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    price: Decimal
    sale: Decimal | None = None
    image_url: str | None = None
    count_product: int


class PaginationSchema(BaseModel):
    offset: int = 0
    limit: int = 20


class OrderStatusUpdateSchema(BaseModel):
    id_order: int
    status: str


class PaymentStatusUpdateSchema(BaseModel):
    id_order: int
    payment_success: bool
    error_message: str | None = None


class OrderResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid_user: UUID
    status_order: str
    status_payment: bool
    created_at: datetime
    total_price: Decimal
    items: List[dict]


class RabbitSendOrderPaymentSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    total_price: Decimal


class RabbitOrderToCatalogSchema(BaseModel):
    id_order: int
    uuid_user: UUID
    products: List[dict]
