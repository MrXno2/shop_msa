from uuid import UUID, uuid4

from sqlalchemy import Integer, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from srv_order.src.db.models.base import Base


class CartORM(Base):
    __tablename__ = "carts_users"

    uuid: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)
    uuid_user: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=False, index=True)
    uuid_product: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=False)
    count_product: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
