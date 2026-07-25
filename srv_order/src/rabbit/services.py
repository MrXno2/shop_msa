from core_app.exception import ProductNotFound 
from srv_order.src.modules.cart.repository import CartRepository
from srv_order.src.modules.order.repository import OrderRepository
from srv_order.src.modules.order.schemas import OrderStatusUpdateSchema, PaymentStatusUpdateSchema
from srv_order.src.db.session import db_session
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from sqlalchemy.exc import IntegrityError
import aio_pika
from srv_order.src.db.models.order import OrderStatusEnum
from srv_order.src.rabbit.schemas import (
    CartCacheDeleteSchema, 
    ProductCacheSchema, 
    RabbitPaymentStatusUpdateSchema, 
    RabbitStockResultSchema
)
from srv_order.src.rabbit.repositories import RabbitCartProductRepository
    

class RabbitCatalogOrderService():
    async def handle_stock_deduction_result(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            order_repo = OrderRepository(db)
            cart_repo = CartRepository(db)
            data = RabbitStockResultSchema.model_validate_json(message.body)
            data_order = OrderStatusUpdateSchema(
                id_order = data.id_order,
                status = data.status_order_type
            )
            if data.status_order_type == OrderStatusEnum.CANCELLED:
                ...
            if data.status_order_type == OrderStatusEnum.CREATED:
                await cart_repo.del_all_product(data.uuid_user)
            await order_repo.update_status_order(data_order)
            await db.commit()


    async def create_product(
        self, 
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = RabbitCartProductRepository(db)
            data = ProductCacheSchema.model_validate_json(message.body)
            product = CartProductCacheORM(
                uuid_product = data.uuid,
                name = data.name,
                price = data.price,
                sale = data.sale,
                image_url = data.image_url
            )
            try:
                await product_repo.create_product(product)
                await db.commit()
            except IntegrityError:
                await db.rollback()



    async def del_product(
        self,
        message: aio_pika.IncomingMessage
    ) -> None:
        async with db_session() as db:
            product_repo = RabbitCartProductRepository(db)
            data = CartCacheDeleteSchema.model_validate_json(message.body)

            await product_repo.del_product(data.uuid_product)
            await db.commit()


    async def full_update_product(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = RabbitCartProductRepository(db)
            data = ProductCacheSchema.model_validate_json(message.body)

            product = await product_repo.get_product(data.uuid)
            if not product:
                raise ProductNotFound()
            
            new_data = data.model_dump()
            new_data["uuid_product"] = new_data.pop("uuid")

            await product_repo.full_update_product(new_data)
            await db.commit()


class RabbitPaymentOrderService:
    async def update_status_payment(
        self, 
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            order_repo = OrderRepository(db)
            data = RabbitPaymentStatusUpdateSchema.model_validate_json(message.body)
            data_to_repo = PaymentStatusUpdateSchema(
                id_order = data.id_order,
                payment_success = data.payment_success
            )
            await order_repo.update_status_payment(data=data_to_repo)
            await db.commit()
