from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.cart_user import CartORM


class CartRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def add_product(self, data_cart: CartORM) -> None:
        self.db.add(data_cart)

    async def del_product(self, uuid_user: UUID, uuid_product: UUID) -> None:
        await self.db.execute(
            delete(CartORM)
            .where(
                CartORM.uuid_user == uuid_user,
                CartORM.uuid_product == uuid_product
            )
        )

    async def del_all_product(self, uuid_user: UUID) -> None:
        await self.db.execute(
            delete(CartORM)
            .where(
                CartORM.uuid_user == uuid_user
            )
        )

    async def get_all_product(self, uuid_user: UUID) -> list[tuple[CartProductCacheORM, CartORM]]:
        result = await self.db.execute(
            select(CartProductCacheORM, CartORM)
            .join(CartORM, CartORM.uuid_product == CartProductCacheORM.uuid_product)
            .where(CartORM.uuid_user == uuid_user)
        )
        
        return [tuple(row) for row in result.all()]
    
    async def get_product(self, uuid_user: UUID, uuid_product: UUID) -> CartORM | None:
        result = await self.db.execute(
            select(CartORM)
            .where(
                CartORM.uuid_user == uuid_user,
                CartORM.uuid_product == uuid_product
            )
            .limit(1)
        )
        return result.scalar_one_or_none()