from uuid import UUID

from fastapi import APIRouter, Depends, status
from srv_catalog.src.dependensies import ProductServiceDep
from srv_catalog.src.modules.product.schemas import (
    ProductCreateSchema,
    ProductListQuerySchema,
    ProductListResponseSchema,
    ProductResponseSchema,
    ProductUpdateSchema,
)

from core_app.security import is_admin_token

router = APIRouter(prefix="/product")


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def lock_create_product(
    req_data: ProductCreateSchema, product_service: ProductServiceDep, payload=Depends(is_admin_token)
) -> None:
    await product_service.create_product(req_data)


@router.get("/get/{uuid_product}", status_code=status.HTTP_200_OK)
async def get_product(uuid_product: UUID, product_service: ProductServiceDep) -> ProductResponseSchema:
    return await product_service.get_product(uuid_product)


@router.get("/get_list", status_code=status.HTTP_200_OK)
async def get_list_products(
    product_service: ProductServiceDep,
    query_params: ProductListQuerySchema = Depends(),
) -> ProductListResponseSchema:
    return await product_service.get_product_list(query_params)


@router.patch("/full_update", status_code=status.HTTP_200_OK)
async def lock_full_update_product(
    req_data: ProductUpdateSchema, product_service: ProductServiceDep, payload=Depends(is_admin_token)
) -> None:
    await product_service.full_update_product(req_data=req_data)


@router.delete("/delete/{uuid_product}", status_code=status.HTTP_204_NO_CONTENT)
async def lock_delete_product(
    uuid_product: UUID, product_service: ProductServiceDep, payload=Depends(is_admin_token)
) -> None:
    await product_service.del_product(uuid_product)
