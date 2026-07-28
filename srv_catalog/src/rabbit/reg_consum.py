from srv_catalog.src.rabbit.services import RabbitCatalogOrderService

from core_app.rabbit import RabbitMain


async def register_consumers_catalog_order(
    rabbit: RabbitMain,
):
    catalog_serv = RabbitCatalogOrderService()

    rabbit.consumer(
        queue="catalog_order.deduct_from_stock",
        routing_key="catalog_order.deduct_from_stock",
        handler=catalog_serv.deduct_from_stock,
    )
