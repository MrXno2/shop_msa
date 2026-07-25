from uuid import UUID
from fastapi import APIRouter, Depends, status
from core_app.security import is_validity_token
from srv_order.src.dependensies import CartServiceDep
from srv_order.src.rabbit.schemas import CartCacheProductSchema


router = APIRouter(prefix="/cart")


@router.post("/add/{uuid_product}", status_code=status.HTTP_201_CREATED)
async def add_product_in_cart(
    uuid_product: UUID, 
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await product_service.add_product(uuid_user=uuid_user, uuid_product=uuid_product)


@router.delete("/del/{uuid_product}", status_code=status.HTTP_200_OK)
async def delete_product_in_cart(
    uuid_product: UUID, 
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await product_service.del_product(uuid_user=uuid_user, uuid_product=uuid_product)


@router.get("/get_all", status_code=status.HTTP_200_OK)
async def get_list_products_cart(
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> list[CartCacheProductSchema]:
    uuid_user = payload.get("uuid")
    return await product_service.get_all_product(uuid_user=uuid_user)
