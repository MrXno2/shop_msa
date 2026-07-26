from datetime import datetime
from uuid import UUID
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from srv_notification.src.db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class NotificationORM(Base):
    __tablename__ = "notifications"

    uuid_user: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=False,
        index=True,
        nullable=False
    )
    title_notification: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    message_notification: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )