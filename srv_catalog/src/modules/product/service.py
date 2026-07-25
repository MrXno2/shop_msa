from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from core_app.exception import ProductNotFound
from srv_catalog.src.db.models.product import ProductORM
from sqlalchemy.exc import IntegrityError
from core_app.rabbit import rabbit_catalog_order
from srv_catalog.src.modules.product.schemas import (
    ProductResponseSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductListQuerySchema,
    ProductListResponseSchema
)
from srv_catalog.src.modules.product.repository import ProductRepository


class ProductService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.product_repo = ProductRepository(db)

    async def create_product(self, req_data: ProductCreateSchema) -> None:
        product = ProductORM(
            name = req_data.name,
            description = req_data.description,
            price = req_data.price,
            sale = req_data.sale,
            stock = req_data.stock,
            image_url = req_data.image_url,
            category_id = req_data.category_id,
        )
        try:
            await self.product_repo.create_product(product)
            await self.db.commit()

            event = ProductResponseSchema.model_validate(product)
            await rabbit_catalog_order.publish("catalog_order.created", event.model_dump(mode="json"))
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(400, "Invalid category_id or duplicate data")


    async def get_product(self, uuid_product: UUID) -> ProductResponseSchema:
        product = await self.product_repo.get_product(uuid_product)
        if not product:
            raise ProductNotFound()
        return ProductResponseSchema.model_validate(product)


    async def del_product(self, uuid_product: UUID) -> None:
        await self.product_repo.del_product(uuid_product)
        await self.db.commit()
        await rabbit_catalog_order.publish("catalog_order.delete", {"uuid_product": str(uuid_product)})


    async def full_update_product(self, req_data: ProductUpdateSchema) -> None:
        result = await self.product_repo.full_update_product(req_data)
        if result is None:
            raise ProductNotFound()
        await self.db.commit()
        event = ProductResponseSchema.model_validate(result)
        await rabbit_catalog_order.publish("catalog_order.update", event.model_dump(mode="json"))


    async def get_product_list(
        self,
        query_params: ProductListQuerySchema
    ) -> ProductListResponseSchema:
        products, total = await self.product_repo.get_products_with_filters(
            query_params
        )

        product_schemas = [
            ProductResponseSchema.model_validate(product)
            for product in products
        ]

        return ProductListResponseSchema(
            items=product_schemas,
            total=total,
            limit=query_params.limit,
            offset=query_params.offset
        )