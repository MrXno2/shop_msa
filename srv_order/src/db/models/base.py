from uuid import UUID, uuid4
from sqlalchemy import Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    uuid: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)