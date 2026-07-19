from srv_order.src.services.cart_product_cache import CartProductCacheService
from srv_order.src.rabbit.rabbit import RabbitMain
from srv_order.src.db.session import db_session, get_db


async def register_consumers_cart_product_cache(
    rabbit: RabbitMain,
):
    order_serv = CartProductCacheService()

    rabbit.consumer(
        queue="cart_product_cache.created",
        routing_key="cart_product_cache.created",
        handler=order_serv.create_product,
    )
    rabbit.consumer(
        queue="cart_product_cache.delete",
        routing_key="cart_product_cache.delete",
        handler=order_serv.del_product,
    )
    rabbit.consumer(
        queue="cart_product_cache.update",
        routing_key="cart_product_cache.update",
        handler=order_serv.full_update_product,
    )