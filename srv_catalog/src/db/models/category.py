from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from srv_catalog.src.db.models.base import Base


class CategoryORM(Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
