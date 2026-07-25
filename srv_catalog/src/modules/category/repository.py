from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from srv_catalog.src.db.models.category import CategoryORM


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
