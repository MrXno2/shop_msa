from uuid import UUID, uuid4
from sqlalchemy import Integer, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from srv_order.src.db.models.base import Base, BaseUUID


class CartORM(BaseUUID):
    __tablename__ = "carts_users"

    uuid_user: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=False,
        index=True
    )
    uuid_product: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        unique=False
    )
    count_product: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )