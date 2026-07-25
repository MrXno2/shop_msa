from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


SortField = Literal["name", "price", "stock"]


class ProductResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str = Field(max_length=255)
    description: str | None = None
    price: Decimal
    sale: Decimal | None = None
    stock: int
    image_url: str | None = Field(None, max_length=1000)
    category_id: UUID


class ProductCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=255)
    description: str | None = None
    price: Decimal
    sale: Decimal | None = None
    stock: int
    image_url: str | None = Field(None, max_length=1000)
    category_id: UUID


class ProductUpdateSchema(BaseModel):
    uuid: UUID
    name: str = Field(max_length=255)
    description: str | None = None
    price: Decimal
    sale: Decimal | None = None
    stock: int
    image_url: str | None = Field(None, max_length=1000)
    category_id: UUID


class ProductListQuerySchema(BaseModel):
    category_id: UUID | None = None
    min_price: Decimal | None = Field(None, ge=0)
    max_price: Decimal | None = Field(None, ge=0)
    in_stock: bool | None = None
    on_sale: bool | None = None
    search: str | None = Field(None, max_length=100)
    sort_by: SortField = "name"
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("min_price", "max_price")
    @classmethod
    def validate_prices(cls, v, info):
        min_price = info.data.get("min_price")
        max_price = info.data.get("max_price")

        if min_price is not None and max_price is not None:
            if min_price > max_price:
                raise ValueError("min_price must be less than or equal to max_price")
        return v


class ProductListResponseSchema(BaseModel):
    items: list[ProductResponseSchema]
    total: int
    limit: int
    offset: int
