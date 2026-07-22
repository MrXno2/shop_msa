from shop_msa.srv_order.src.routers.order import OrderService
from shop_msa.srv_order.src.services.rabbit_catalog_order import RabbitCatalogOrderService, RabbitPaymentOrderService
from srv_order.src.rabbit.rabbit import RabbitMain
from srv_order.src.db.session import db_session, get_db


async def register_consumers_catalog_order(
    rabbit: RabbitMain,
):
    order_serv = RabbitCatalogOrderService()

    rabbit.consumer(
        queue="catalog_order.created",
        routing_key="catalog_order.created",
        handler=order_serv.create_product,
    )
    rabbit.consumer(
        queue="catalog_order.delete",
        routing_key="catalog_order.delete",
        handler=order_serv.del_product,
    )
    rabbit.consumer(
        queue="catalog_order.update",
        routing_key="catalog_order.update",
        handler=order_serv.full_update_product,
    )

async def register_consumers_payment_order(
    rabbit: RabbitMain,
):
    payment_serv = RabbitPaymentOrderService()

    rabbit.consumer(
        queue="payment_order.update_status_payment",
        routing_key="payment_order.update_status_payment",
        handler=payment_serv.update_status_payment,
    )
