from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from srv_order.src.db.session import get_db
from srv_order.src.modules.cart.service import CartService
from srv_order.src.modules.order.service import OrderService


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_product_servise(db: DbDep) -> CartService:
    return CartService(db)

CartServiceDep = Annotated[CartService, Depends(get_product_servise)]


async def get_order_service(db: DbDep) -> OrderService:
    return OrderService(db)

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]