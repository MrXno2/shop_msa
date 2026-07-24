from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from core_app.security import is_admin_token
from srv_catalog.src.db.models.category import CategoryORM
from srv_catalog.src.dependensies import DbDep
from srv_catalog.src.routers.product import ProductRepository


router = APIRouter(prefix="/category")


class CategoryRequestSchema(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None


class CategoryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    uuid: UUID
    name: str = Field(max_length=255)
    description: str | None = None


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def add_category(self, category_data: CategoryORM) -> None:
        self.db.add(category_data)


    async def del_category(self, uuid_category: UUID) -> None:
        await self.db.execute(
            delete(CategoryORM)
            .where(CategoryORM.uuid == uuid_category)
        )


    async def get_all_categories(self) -> list[CategoryORM]:
        result = await self.db.execute(
            select(CategoryORM)
        )
        return list(result.scalars().all())


    async def get_category(self, uuid_category: UUID) -> CategoryORM | None:
        result = await self.db.execute(
            select(CategoryORM)
            .where(CategoryORM.uuid == uuid_category)
            .limit(1)
        )
        return result.scalar_one_or_none()


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.category_repo = CategoryRepository(db=db)
        self.product_repo = ProductRepository(db=db)


    async def add_category(self, category_data: CategoryRequestSchema):
        new_category = CategoryORM(
            name = category_data.name,
            description = category_data.description
        )
        try:
            await self.category_repo.add_category(category_data=new_category)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(400, "Invalid category_id or duplicate data")


    async def del_category(self, uuid_category: UUID):
        product = await self.product_repo.get_product_uuid_category(uuid_category=uuid_category)
        if product is not None:
            raise HTTPException(409, "Category has products")
        await self.category_repo.del_category(uuid_category)
        await self.db.commit()


    async def get_all_category(self) -> list[CategoryResponseSchema]:
        all_categories = await self.category_repo.get_all_categories()
        return [CategoryResponseSchema.model_validate(category) for category in all_categories]
    

    async def get_one_category(self, uuid_category: UUID) -> CategoryResponseSchema:
        category = await self.category_repo.get_category(uuid_category=uuid_category)
        if category is None:
            raise HTTPException(404, "Category not found")
        return CategoryResponseSchema.model_validate(category)



async def get_category_service(db: DbDep) -> CategoryService:
    return CategoryService(db=db)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


@router.post("/add")
async def set_category_in_catalog(
    category_data: CategoryRequestSchema,
    category_servise: CategoryServiceDep,
    payload = Depends(is_admin_token)
) -> None:
    await category_servise.add_category(category_data=category_data)


@router.delete("/del/{uuid_category}")
async def delete_category_in_catalog(
    uuid_category: UUID,
    category_servise: CategoryServiceDep,
    payload = Depends(is_admin_token)
) -> None:
    await category_servise.del_category(uuid_category)


@router.get("/all")
async def get_all_category(
    category_servise: CategoryServiceDep
) -> list[CategoryResponseSchema]:
    return await category_servise.get_all_category()