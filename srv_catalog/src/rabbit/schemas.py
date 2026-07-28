from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RabbitRequestOrderProductsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    price: Decimal
    sale: Decimal | None = None
    image_url: str | None = None
    count_product: int


class RabbitRequestOrderSchema(BaseModel):
    id_order: int
    uuid_user: UUID
    products: list[RabbitRequestOrderProductsSchema]


class RabbitResponseCatalogSchema(BaseModel):
    id_order: int
    uuid_user: UUID
    status_order_type: str
