from decimal import Decimal
from typing import Annotated
from uuid import UUID
from sqlalchemy import Result, and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from core_app.security import is_admin_token
from core_app.exception import ProductNotFound 
from srv_catalog.src.db.models.product import ProductORM
from srv_catalog.src.dependensies import DbDep
from sqlalchemy.exc import IntegrityError
from srv_catalog.src.rabbit.rabbit import rabbit_cart_product_cache


router = APIRouter(prefix="/product")


class ProductSchema(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID
    name: str = Field(max_length=255)
    description: str | None = None
    price: Decimal
    sale: Decimal | None = None
    stock: int
    image_url: str | None = Field(None, max_length=1000)
    category_id: UUID


class ProductCreateSchema(BaseModel):
    model_config = {"from_attributes": True}

    name: str = Field(max_length=255)
    description: str | None = None
    price: Decimal
    sale: Decimal | None = None
    stock: int
    image_url: str | None = Field(None, max_length=1000)
    category_id: UUID


class ProductListQuerySchema(BaseModel):
    category_id: str | None = None
    min_price: Decimal | None = Field(None, ge=0)
    max_price: Decimal | None = Field(None, ge=0)
    in_stock: bool | None = None
    on_sale: bool | None = None
    search: str | None = Field(None, max_length=100)
    sort_by: str = Field(default="name")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @field_validator("min_price", "max_price")
    @classmethod
    def validate_prices(cls, v, info):
        min_price = info.data.get("min_price")
        max_price = info.data.get("max_price")
        
        if min_price is not None and max_price is not None:
            if min_price > max_price:
                raise ValueError("min_price must be less than or equal to max_price")
        return v
    

class ProductListResponse(BaseModel):
    items: list[ProductSchema]
    total: int
    limit: int
    offset: int


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


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


    async def full_update_product(self, req_data: ProductSchema) -> None:
        update_data = req_data.model_dump(exclude={"uuid"})
        await self.db.execute(
            update(ProductORM)
            .where(ProductORM.uuid == req_data.uuid)
            .values(**update_data)
        )


    async def get_products_with_filters(
        self, 
        filters: ProductListQuerySchema
    ) -> tuple[list[ProductORM], int]:
        """Возвращает (список товаров, общее количество)"""
        
        # 1. Базовый запрос
        query = select(ProductORM)
        
        # 2. Применяем фильтры
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
        
        # 3. Сортировка
        sort_field = getattr(ProductORM, filters.sort_by, None)
        if sort_field:
            if filters.sort_order == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(ProductORM.name))
        
        # 4. Пагинация
        query = query.offset(filters.offset).limit(filters.limit)
        
        # 5. Выполняем запрос
        result = await self.db.execute(query)
        products = list(result.scalars().all())
        
        # 6. Подсчёт общего количества (для пагинации)
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

            event = ProductSchema.model_validate(product)
            await rabbit_cart_product_cache.publish("cart_product_cache.created", event.model_dump(mode="json"))
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(400, "Invalid category_id or duplicate data")

    
    async def get_product(self, uuid_product: UUID) -> ProductSchema:
        product = await self.product_repo.get_product(uuid_product)
        if not product:
            raise ProductNotFound()
        return ProductSchema.model_validate(product)
    

    async def del_product(self, uuid_product: UUID) -> None:
        await self.product_repo.del_product(uuid_product)
        await self.db.commit()
        await rabbit_cart_product_cache.publish("cart_product_cache.delete", {"uuid_product": str(uuid_product)})


    async def full_update_product(self, req_data: ProductSchema) -> None:
        product = await self.product_repo.get_product(req_data.uuid)
        if not product:
            raise ProductNotFound()
        await self.product_repo.full_update_product(req_data)
        await self.db.commit()
        event = ProductSchema.model_validate(product)
        await rabbit_cart_product_cache.publish("cart_product_cache.update", event.model_dump(mode="json"))


    async def get_product_list(
        self, 
        query_params: ProductListQuerySchema
    ) -> ProductListResponse:
        products, total = await self.product_repo.get_products_with_filters(
            query_params
        )
        
        # Превращаем ORM → Pydantic
        product_schemas = [
            ProductSchema.model_validate(product) 
            for product in products
        ]
        
        return ProductListResponse(
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
) -> ProductSchema:
    return await product_service.get_product(uuid_product)


@router.get("/get_list", status_code=status.HTTP_200_OK)
async def get_list_products(
    product_service: ProductServiceDep,
    query_params: ProductListQuerySchema = Depends(),
) -> ProductListResponse:
    return await product_service.get_product_list(query_params)


@router.patch("/full_update", status_code=status.HTTP_200_OK)
async def lock_full_update_product(
    req_data: ProductSchema,
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
