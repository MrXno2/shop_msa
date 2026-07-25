from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from srv_order.src.db.models.order import OrderORM
from srv_order.src.modules.order.schemas import (
    PaginationSchema,
    OrderStatusUpdateSchema,
    PaymentStatusUpdateSchema
)


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
