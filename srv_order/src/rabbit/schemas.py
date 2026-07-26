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


class RabbitSendOrderPaymentSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    total_price: Decimal


class RabbitOrderToCatalogSchema(BaseModel):
    id_order: int
    uuid_user: UUID
    products: List[dict]


class RabbitPaymentStatusUpdateSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    payment_success: bool
    error_message: str | None = None


class ProductCacheSchema(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID
    name: str
    price: Decimal
    sale: Decimal | None = None
    image_url: str | None = None


class RabbitStockResultSchema(BaseModel):
    id_order: int
    uuid_user: UUID
    status_order_type: str


class CartCacheDeleteSchema(BaseModel):
    model_config = {"from_attributes": True}

    uuid_product: UUID


class RabbitAddNotificationSchema(BaseModel):
    uuid_user: UUID
    title_notification: str
    message_notification: str