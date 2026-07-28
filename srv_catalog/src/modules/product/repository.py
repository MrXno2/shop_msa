from uuid import UUID

from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from srv_catalog.src.db.models.product import ProductORM
from srv_catalog.src.modules.product.schemas import (
    ProductListQuerySchema,
    ProductUpdateSchema,
)
from srv_catalog.src.rabbit.schemas import RabbitRequestOrderProductsSchema


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def deduct_from_stock(self, product: RabbitRequestOrderProductsSchema) -> ProductORM | None:
        result = await self.db.execute(
            update(ProductORM)
            .where(ProductORM.uuid == product.uuid, ProductORM.stock >= product.count_product)
            .values(stock=ProductORM.stock - product.count_product)
            .returning(ProductORM)
        )
        return result.scalar_one_or_none()

    async def get_product_uuid_category(self, uuid_category: UUID) -> ProductORM | None:
        result = await self.db.execute(select(ProductORM).where(ProductORM.category_id == uuid_category).limit(1))
        return result.scalar_one_or_none()

    async def create_product(self, data_product: ProductORM) -> None:
        self.db.add(data_product)

    async def get_product(self, uuid_product: UUID) -> ProductORM | None:
        product = await self.db.execute(select(ProductORM).where(ProductORM.uuid == uuid_product).limit(1))
        return product.scalar_one_or_none()

    async def del_product(self, uuid_product: UUID) -> None:
        await self.db.execute(delete(ProductORM).where(ProductORM.uuid == uuid_product))

    async def full_update_product(self, req_data: ProductUpdateSchema) -> ProductORM | None:
        update_data = req_data.model_dump(exclude={"uuid"})
        result = await self.db.execute(
            update(ProductORM).where(ProductORM.uuid == req_data.uuid).values(**update_data).returning(ProductORM)
        )
        return result.scalar_one_or_none()

    async def get_products_with_filters(self, filters: ProductListQuerySchema) -> tuple[list[ProductORM], int]:
        query = select(ProductORM)

        conditions = []

        if filters.category_id:
            conditions.append(ProductORM.category_id == filters.category_id)

        if filters.min_price is not None:
            conditions.append(ProductORM.price >= filters.min_price)

        if filters.max_price:
            conditions.append(ProductORM.price <= filters.max_price)

        if filters.in_stock:
            conditions.append(ProductORM.stock > 0)

        if filters.on_sale:
            conditions.append(ProductORM.sale.is_not(None))

        if filters.search:
            search_pattern = f"%{filters.search}%"
            conditions.append(or_(ProductORM.name.ilike(search_pattern), ProductORM.description.ilike(search_pattern)))

        if conditions:
            query = query.where(and_(*conditions))

        sort_field = getattr(ProductORM, filters.sort_by, None)
        if sort_field:
            if filters.sort_order == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(ProductORM.name))

        query = query.offset(filters.offset).limit(filters.limit)

        result = await self.db.execute(query)
        products = list(result.scalars().all())

        count_query = select(func.count()).select_from(ProductORM)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = await self.db.scalar(count_query)

        return products, total or 0
