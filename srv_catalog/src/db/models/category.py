from sqlalchemy import String, Text
from srv_catalog.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class CategoryORM(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)