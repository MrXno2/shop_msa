from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from srv_catalog.src.db.session import get_db
from srv_catalog.src.modules.category.service import CategoryService
from srv_catalog.src.modules.product.service import ProductService


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_category_service(db: DbDep) -> CategoryService:
    return CategoryService(db=db)

CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]


async def get_product_servise(db: DbDep) -> ProductService:
    return ProductService(db)

ProductServiceDep = Annotated[ProductService, Depends(get_product_servise)]
