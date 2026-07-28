from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM


class RabbitCartProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_product(self, data_product: CartProductCacheORM) -> None:
        self.db.add(data_product)

    async def del_product(self, uuid_product: UUID) -> None:
        await self.db.execute(delete(CartProductCacheORM).where(CartProductCacheORM.uuid_product == uuid_product))

    async def full_update_product(self, req_data: dict) -> None:
        await self.db.execute(
            update(CartProductCacheORM)
            .where(CartProductCacheORM.uuid_product == req_data["uuid_product"])
            .values(**req_data)
        )

    async def get_product(self, uuid_product: UUID) -> CartProductCacheORM | None:
        product = await self.db.execute(
            select(CartProductCacheORM).where(CartProductCacheORM.uuid_product == uuid_product).limit(1)
        )
        return product.scalar_one_or_none()
