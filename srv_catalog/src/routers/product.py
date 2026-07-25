from typing import Annotated
from uuid import UUID
from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from core_app.security import is_admin_token
from core_app.exception import ProductNotFound
from srv_catalog.src.db.models.product import ProductORM
from srv_catalog.src.dependensies import DbDep
from sqlalchemy.exc import IntegrityError
from core_app.rabbit import rabbit_catalog_order
from srv_catalog.src.schemas import (
    ProductResponseSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductListQuerySchema,
    ProductListResponseSchema,
    RabbitRequestOrderProductsSchema,
)


router = APIRouter(prefix="/product")


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def deduct_from_stock(self, product: RabbitRequestOrderProductsSchema) -> ProductORM | None:
        result = await self.db.execute(
            update(ProductORM)
            .where(
                ProductORM.uuid == product.uuid,
                ProductORM.stock >= product.count_product
            )
            .values(stock = ProductORM.stock - product.count_product)
            .returning(ProductORM)
        )
        return result.scalar_one_or_none()


    async def get_product_uuid_category(self, uuid_category: UUID) -> ProductORM | None:
        result = await self.db.execute(
            select(ProductORM)
            .where(ProductORM.category_id == uuid_category)
            .limit(1)
        )
        return result.scalar_one_or_none()


    async def create_product(self, data_product: ProductORM) -> None:
        self.db.add(data_product)


    async def get_product(self, uuid_product: UUID) -> ProductORM | None:
        product = await self.db.execute(
            select(ProductORM)
            .where(ProductORM.uuid == uuid_product)
            .limit(1)
        )
        return product.scalar_one_or_none()


    async def del_product(self, uuid_product: UUID) -> None:
        await self.db.execute(
            delete(ProductORM)
            .where(ProductORM.uuid == uuid_product)
        )


    async def full_update_product(self, req_data: ProductUpdateSchema) -> ProductORM | None:
        update_data = req_data.model_dump(exclude={"uuid"})
        result = await self.db.execute(
            update(ProductORM)
            .where(ProductORM.uuid == req_data.uuid)
            .values(**update_data)
            .returning(ProductORM)
        )
        return result.scalar_one_or_none()


    async def get_products_with_filters(
        self,
        filters: ProductListQuerySchema
    ) -> tuple[list[ProductORM], int]:
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
            conditions.append(
                or_(
                    ProductORM.name.ilike(search_pattern),
                    ProductORM.description.ilike(search_pattern)
                )
            )

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


async def get_product_servise(db: DbDep) -> ProductService:
    return ProductService(db)


ProductServiceDep = Annotated[ProductService, Depends(get_product_servise)]


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def lock_create_product(
    req_data: ProductCreateSchema,
    product_service: ProductServiceDep,
    payload = Depends(is_admin_token)
) -> None:
    await product_service.create_product(req_data)


@router.get("/get/{uuid_product}", status_code=status.HTTP_200_OK)
async def get_product(
    uuid_product: UUID,
    product_service: ProductServiceDep
) -> ProductResponseSchema:
    return await product_service.get_product(uuid_product)


@router.get("/get_list", status_code=status.HTTP_200_OK)
async def get_list_products(
    product_service: ProductServiceDep,
    query_params: ProductListQuerySchema = Depends(),
) -> ProductListResponseSchema:
    return await product_service.get_product_list(query_params)


@router.patch("/full_update", status_code=status.HTTP_200_OK)
async def lock_full_update_product(
    req_data: ProductUpdateSchema,
    product_service: ProductServiceDep,
    payload = Depends(is_admin_token)
) -> None:
    await product_service.full_update_product(req_data=req_data)


@router.delete("/delete/{uuid_product}", status_code=status.HTTP_200_OK)
async def lock_delete_product(
    uuid_product: UUID,
    product_service: ProductServiceDep,
    payload = Depends(is_admin_token)
) -> None:
    await product_service.del_product(uuid_product)
