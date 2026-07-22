from datetime import datetime
from decimal import Decimal
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core_app.security import is_admin_token, is_validity_token
from srv_order.src.db.models.order import OrderORM, OrderStatus
from srv_order.src.dependensies import DbDep
from srv_order.src.routers.cart import CartRepository, CartCacheProductSchema
from srv_order.src.rabbit.rabbit import rabbit_payment_order



router = APIRouter(prefix="/order")


class PaginationSchema(BaseModel):
    offset: int
    limit: int


class PaymentStatusSchema(BaseModel):
    id_order: int
    payment_success: bool
    error_message: str | None = None

class OrderStatusSchema(BaseModel):
    id_order: int
    status: str

class RabbitSendOrderPaymentSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    total_price: Decimal


class OrderSchema(BaseModel):
    """Схема заказа для ответа API"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid_user: UUID
    status_order: str
    status_payment: bool
    created_at: datetime
    total_price: Decimal
    items: List[dict]


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_order(self, order: OrderORM) -> None:
        self.db.add(order)

    async def update_status_order(self, data: OrderStatusSchema) -> None:
        await self.db.execute(
            update(OrderORM)
            .where(OrderORM.id == data.id_order)
            .values(status_order = data.status)
        )

    async def update_status_payment(self, data: PaymentStatusSchema) -> None:
        await self.db.execute(
            update(OrderORM)
            .where(OrderORM.id == data.id_order)
            .values(status_payment = data.payment_success)
        )

    async def get_order(self, uuid_user: UUID, id_order: int) -> OrderORM | None:
        result = await self.db.execute(
            select(OrderORM)
            .where(
                OrderORM.uuid_user == uuid_user,
                OrderORM.id == id_order
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_all_orders(
        self, 
        pagination: PaginationSchema
    ) -> list[OrderORM]:
        result = await self.db.execute(
            select(OrderORM)
            .limit(pagination.limit)
            .offset(pagination.offset)
        )
        return list(result.scalars().all())


class OrderService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)

    async def get_all_orders(
        self, 
        pagination: PaginationSchema
    ) -> list[OrderSchema]:
        result = await self.order_repo.get_all_orders(pagination)
        return [OrderSchema.model_validate(val) for val in result]

    async def update_status_order(self, data: OrderStatusSchema) -> None:
        await self.order_repo.update_status_order(data)
        await self.db.commit()
        # отравка уведы через брокер

    async def update_status_payment(self, data: PaymentStatusSchema) -> None:
        await self.order_repo.update_status_payment(data)
        await self.db.commit()
        # отравка уведы через брокер

    async def pay_for_order(self, uuid_user: UUID, id_order: int) -> None:
        order = await self.order_repo.get_order(uuid_user=uuid_user, id_order=id_order)
        if order is None:
            raise HTTPException(status.HTTP_404, "Order not found for this user")
        data_send = RabbitSendOrderPaymentSchema(
            uuid_user=order.uuid_user,
            id_order=order.id,
            total_price=order.total_price
        )
        await rabbit_payment_order.publish(
            "payment_order.payment", 
            data_send.model_dump()
        ) # отправка в rabbit оплаты


    async def create_order(self, uuid_user: UUID):
        card_user = await self.cart_repo.get_all_product(uuid_user=uuid_user)
        if len(card_user) == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Card 0 item")

        product_schemas = []
        count_price = 0
        for cache_product, cart in card_user:

            item = CartCacheProductSchema(
                uuid=cache_product.uuid_product,
                name=cache_product.name,
                price=cache_product.price,
                sale=cache_product.sale,
                image_url=cache_product.image_url,
                count_product=cart.count_product
            )
            price_total_product = cache_product.price / 100 * (100 - cache_product.sale) * cart.count_product
            count_price += round(price_total_product, 2)

            product_schemas.append(item.model_dump())

        order = OrderORM(
            uuid_user = uuid_user,
            total_price = count_price,
            items = product_schemas
        )
        try:
            await self.order_repo.create_order(order)
            await self.cart_repo.del_all_product(uuid_user)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, "conflict")


async def get_order_service(db: DbDep) -> OrderService:
    return OrderService(db)

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


# просто берем uuid из токена и делаем заказ по его корзине
@router.post("/create")
async def create_order(
    order_service: OrderServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await order_service.create_order(uuid_user)


# админская ручка где все заказы
@router.patch("/update_status_order")
async def update_status_order(
    order_service: OrderServiceDep,
    data: OrderStatusSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_order(data)


@router.patch("/update_status_payment")
async def update_status_payment(
    order_service: OrderServiceDep,
    data: PaymentStatusSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_payment(data)


@router.get("/list")
async def get_all_orders(
    order_service: OrderServiceDep,
    pagination: PaginationSchema,
    payload = Depends(is_admin_token)
) -> list[OrderSchema]:
    return await order_service.get_all_orders(pagination)


