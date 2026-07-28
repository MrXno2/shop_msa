import aio_pika
from sqlalchemy.exc import IntegrityError
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.order import OrderStatusEnum
from srv_order.src.db.session import db_session
from srv_order.src.modules.cart.repository import CartRepository
from srv_order.src.modules.order.repository import OrderRepository
from srv_order.src.modules.order.schemas import (
    OrderStatusUpdateSchema,
    PaymentStatusUpdateSchema,
)
from srv_order.src.rabbit.repositories import RabbitCartProductRepository
from srv_order.src.rabbit.schemas import (
    CartCacheDeleteSchema,
    ProductCacheSchema,
    RabbitAddNotificationSchema,
    RabbitPaymentStatusUpdateSchema,
    RabbitStockResultSchema,
)

from core_app.exception import ProductNotFound
from core_app.messages_notification import messages
from core_app.rabbit import rabbit_all_notification


class RabbitCatalogOrderService:
    async def handle_stock_deduction_result(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            order_repo = OrderRepository(db)
            cart_repo = CartRepository(db)
            data = RabbitStockResultSchema.model_validate_json(message.body)
            data_order = OrderStatusUpdateSchema(id_order=data.id_order, status=data.status_order_type)
            notif = RabbitAddNotificationSchema(
                uuid_user=data.uuid_user,
                title_notification=f"{messages.NAME_ORDER} {data.id_order}",
                message_notification=messages.DESC_ORDER_CREATED,
            )
            if data.status_order_type == OrderStatusEnum.CANCELLED:
                notif.message_notification = messages.DESC_ORDER_CANCELED
            if data.status_order_type == OrderStatusEnum.CREATED:
                await cart_repo.del_all_product(data.uuid_user)
            await order_repo.update_status_order(data_order)
            await db.commit()
            await rabbit_all_notification.publish("all_notification.add", notif.model_dump(mode="json"))

    async def create_product(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = RabbitCartProductRepository(db)
            data = ProductCacheSchema.model_validate_json(message.body)
            product = CartProductCacheORM(
                uuid_product=data.uuid,
                name=data.name,
                price=data.price,
                sale=data.sale,
                image_url=data.image_url,
            )
            try:
                await product_repo.create_product(product)
                await db.commit()
            except IntegrityError:
                await db.rollback()

    async def del_product(self, message: aio_pika.IncomingMessage) -> None:
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
            data_to_repo = PaymentStatusUpdateSchema(id_order=data.id_order, payment_success=data.payment_success)
            await order_repo.update_status_payment(data=data_to_repo)
            await db.commit()
