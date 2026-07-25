from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class RabbitWalletUserSchema(BaseModel):
    uuid_user: UUID
    number: str


class RabbitRequestOrderPaymentSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    total_price: Decimal


class RabbitResponseOrderPaymentSchema(BaseModel):
    id_order: int
    payment_success: bool
    error_message: str | None = None