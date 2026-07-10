from datetime import datetime
from sqlalchemy import DateTime, String, Text, func
from srv_auth.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class UserORM(Base):
    __tablename__ = "users"

    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    country: Mapped[str] = mapped_column(String(155), nullable=True)
    city: Mapped[str] = mapped_column(String(155), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())