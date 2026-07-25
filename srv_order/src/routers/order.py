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
from srv_order.src.db.models.order import OrderORM, OrderStatusEnum
from srv_order.src.dependensies import DbDep
from srv_order.src.routers.cart import CartRepository
from srv_order.src.schemas import (
    CartCacheProductSchema,
    PaginationSchema,
    OrderStatusUpdateSchema,
    PaymentStatusUpdateSchema,
    OrderResponseSchema,
    RabbitSendOrderPaymentSchema,
    RabbitOrderToCatalogSchema,
)
from core_app.rabbit import rabbit_payment_order, rabbit_catalog_order



router = APIRouter(prefix="/order")


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.db.add(order)
        await self.db.flush()
        return order

    async def update_status_order(self, data: OrderStatusUpdateSchema) -> None:
        await self.db.execute(
            update(OrderORM)
            .where(OrderORM.id == data.id_order)
            .values(status_order = data.status)
        )

    async def update_status_payment(self, data: PaymentStatusUpdateSchema) -> None:
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
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Card 0 item")

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


async def get_order_service(db: DbDep) -> OrderService:
    return OrderService(db)

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post("/create")
async def create_order(
    order_service: OrderServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await order_service.create_order(uuid_user)


@router.patch("/update_status_order")
async def lock_update_status_order(
    order_service: OrderServiceDep,
    data: OrderStatusUpdateSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_order(data)


@router.patch("/update_status_payment")
async def lock_update_status_payment(
    order_service: OrderServiceDep,
    data: PaymentStatusUpdateSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_payment(data)


@router.post("/pay_order/{id_order}")
async def pay_for_order(
    order_service: OrderServiceDep,
    id_order: int,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await order_service.pay_for_order(uuid_user=uuid_user, id_order=id_order)


@router.get("/list")
async def lock_get_all_orders(
    order_service: OrderServiceDep,
    pagination: PaginationSchema = Depends(),
    payload = Depends(is_admin_token)
) -> list[OrderResponseSchema]:
    return await order_service.get_all_orders(pagination)
