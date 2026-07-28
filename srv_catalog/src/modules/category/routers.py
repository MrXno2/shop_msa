from uuid import UUID

from fastapi import APIRouter, Depends
from srv_catalog.src.dependensies import CategoryServiceDep
from srv_catalog.src.modules.category.schemas import (
    CategoryRequestSchema,
    CategoryResponseSchema,
)

from core_app.security import is_admin_token

router = APIRouter(prefix="/category")


@router.post("/add")
async def set_category_in_catalog(
    category_data: CategoryRequestSchema, category_servise: CategoryServiceDep, payload=Depends(is_admin_token)
) -> None:
    await category_servise.add_category(category_data=category_data)


@router.delete("/del/{uuid_category}")
async def delete_category_in_catalog(
    uuid_category: UUID, category_servise: CategoryServiceDep, payload=Depends(is_admin_token)
) -> None:
    await category_servise.del_category(uuid_category)


@router.get("/all")
async def get_all_category(category_servise: CategoryServiceDep) -> list[CategoryResponseSchema]:
    return await category_servise.get_all_category()
