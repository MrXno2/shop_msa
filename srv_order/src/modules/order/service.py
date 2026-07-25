from decimal import Decimal
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from srv_order.src.db.models.order import OrderORM
from srv_order.src.modules.cart.repository import CartRepository
from srv_order.src.modules.order.schemas import (
    PaginationSchema,
    OrderStatusUpdateSchema,
    PaymentStatusUpdateSchema,
    OrderResponseSchema 
)
from srv_order.src.rabbit.schemas import (
    RabbitSendOrderPaymentSchema,
    RabbitOrderToCatalogSchema,
    CartCacheProductSchema
)
from core_app.rabbit import rabbit_payment_order, rabbit_catalog_order
from srv_order.src.modules.order.repository import OrderRepository


class OrderService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)

    async def get_all_orders(
        self, 
        pagination: PaginationSchema
    ) -> list[OrderResponseSchema]:
        result = await self.order_repo.get_all_orders(pagination)
        return [OrderResponseSchema.model_validate(val) for val in result]

    async def update_status_order(self, data: OrderStatusUpdateSchema) -> None:
        await self.order_repo.update_status_order(data)
        await self.db.commit()

    async def update_status_payment(self, data: PaymentStatusUpdateSchema) -> None:
        await self.order_repo.update_status_payment(data)
        await self.db.commit()

    async def pay_for_order(self, uuid_user: UUID, id_order: int) -> None:
        order = await self.order_repo.get_order(uuid_user=uuid_user, id_order=id_order)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found for this user")
        data_send = RabbitSendOrderPaymentSchema(
            uuid_user=order.uuid_user,
            id_order=order.id,
            total_price=order.total_price
        )
        await rabbit_payment_order.publish(
            "payment_order.payment", 
            data_send.model_dump(mode='json')
        )


    async def create_order(self, uuid_user: UUID):
        card_user = await self.cart_repo.get_all_product(uuid_user=uuid_user)
        if len(card_user) == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Card 0 item")

        product_schemas = []
        count_price = Decimal("0.00")
        for cache_product, cart in card_user:

            item = CartCacheProductSchema(
                uuid=cache_product.uuid_product,
                name=cache_product.name,
                price=cache_product.price,
                sale=cache_product.sale,
                image_url=cache_product.image_url,
                count_product=cart.count_product
            )
            sale = cache_product.sale or 0
            price_total_product = cache_product.price / 100 * (100 - sale) * cart.count_product
            count_price += price_total_product.quantize(Decimal("0.01"))
            product_schemas.append(item.model_dump(mode="json"))

        order = OrderORM(
            uuid_user = uuid_user,
            total_price = count_price,
            items = product_schemas
        )
        try:
            new_order = await self.order_repo.create_order(order)
            rabbit_mess = RabbitOrderToCatalogSchema(
                id_order = new_order.id,
                uuid_user = uuid_user,
                products = new_order.items
            )
            await self.db.commit()
            await rabbit_catalog_order.publish(
                "catalog_order.deduct_from_stock", 
                rabbit_mess.model_dump(mode="json")
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "conflict")