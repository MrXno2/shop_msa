from core_app.rabbit import RabbitMain
from srv_notification.src.rabbit.services import RabbitNotificationService


async def register_consumers_all_notification(
    rabbit: RabbitMain,
):
    notif_serv = RabbitNotificationService()

    rabbit.consumer(
        queue="all_notification.add",
        routing_key="all_notification.add",
        handler=notif_serv.add_notification,
    )
