from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from srv_order.src.db.models.base import Base


class CartProductCacheORM(Base):
    __tablename__ = "cart_products_cache"

    uuid_product: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True, unique=True, primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sale: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=True)
