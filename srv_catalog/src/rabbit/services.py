from decimal import Decimal

from core_app.rabbit import rabbit_catalog_order
import aio_pika
from srv_catalog.src.db.session import db_session
from srv_catalog.src.modules.product.repository import ProductRepository
from core_app.enums import OrderStatusEnum
from srv_catalog.src.rabbit.schemas import (
    RabbitRequestOrderSchema,
    RabbitResponseCatalogSchema,
)


class RabbitCatalogOrderService:
    async def deduct_from_stock(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = ProductRepository(db)
            data = RabbitRequestOrderSchema.model_validate_json(message.body)
            resp_rabbit = RabbitResponseCatalogSchema(
                id_order = data.id_order,
                uuid_user = data.uuid_user,
                status_order_type = OrderStatusEnum.CREATED
            )
            success = True
            for product in data.products:
                update_product_stock = await product_repo.deduct_from_stock(product)

                if update_product_stock is None:
                    success = False
                    break

                actual_sale = update_product_stock.sale if update_product_stock.sale is not None else Decimal('0')
                cached_sale = product.sale if product.sale is not None else Decimal('0')

                if (update_product_stock.price != product.price or
                    actual_sale != cached_sale):
                    success = False
                    break

            if success:
                await db.commit()
            else:
                await db.rollback()
                resp_rabbit.status_order_type = OrderStatusEnum.CANCELLED

            await rabbit_catalog_order.publish(
                "catalog_order.handle_stock_deduction_result",
                resp_rabbit.model_dump(mode="json")
            )  
