import aio_pika
from srv_notification.src.rabbit.schemas import RabbitAddNotificationSchema
from srv_notification.src.db.session import db_session
from srv_notification.src.modules.notification.routers import NotificationRepository
from srv_notification.src.db.models.notification import NotificationORM


class RabbitNotificationService:
    async def add_notification(
            self,
            message: aio_pika.IncomingMessage
    ) -> None:
        async with db_session() as db:
            notif_repo = NotificationRepository(db)
            data = RabbitAddNotificationSchema.model_validate_json(message.body)
            notif = NotificationORM(
                uuid_user = data.uuid_user,
                title_notification = data.title_notification,
                message_notification = data.message_notification
            )
            await notif_repo.add_notification(notif=notif)
            await db.commit()