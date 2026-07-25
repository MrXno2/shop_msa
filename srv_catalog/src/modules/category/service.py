from uuid import UUID
from srv_catalog.src.modules.product.repository import ProductRepository
from sqlalchemy.ext.asyncio import AsyncSession
from srv_catalog.src.modules.category.repository import CategoryRepository
from srv_catalog.src.modules.category.schemas import CategoryRequestSchema, CategoryResponseSchema
from srv_catalog.src.db.models.category import CategoryORM
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status


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
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid category_id or duplicate data")


    async def del_category(self, uuid_category: UUID):
        product = await self.product_repo.get_product_uuid_category(uuid_category=uuid_category)
        if product is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Category has products")
        await self.category_repo.del_category(uuid_category)
        await self.db.commit()


    async def get_all_category(self) -> list[CategoryResponseSchema]:
        all_categories = await self.category_repo.get_all_categories()
        return [CategoryResponseSchema.model_validate(category) for category in all_categories]
    

    async def get_one_category(self, uuid_category: UUID) -> CategoryResponseSchema:
        category = await self.category_repo.get_category(uuid_category=uuid_category)
        if category is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
        return CategoryResponseSchema.model_validate(category)