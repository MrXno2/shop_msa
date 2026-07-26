from uuid import UUID
from pydantic import BaseModel


class RabbitAddNotificationSchema(BaseModel):
    uuid_user: UUID
    title_notification: str
    message_notification: str