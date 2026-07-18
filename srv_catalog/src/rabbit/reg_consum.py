from srv_catalog.src.rabbit.rabbit import RabbitMain
from srv_catalog.src.rabbit.services import OrderRabbitService


def register_consumers_cart_product_cache(rabbit: RabbitMain):
    order_serv = OrderRabbitService()

    rabbit.consumer(
        queue="notifications.order_created",
        routing_key="order.created",
        handler=order_serv.handle_created,
    )