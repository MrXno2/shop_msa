from fastapi import APIRouter, Depends
from core_app.security import is_admin_token, is_validity_token
from srv_order.src.dependensies import OrderServiceDep
from srv_order.src.modules.order.schemas import (
    PaginationSchema,
    OrderStatusUpdateSchema,
    PaymentStatusUpdateSchema,
    OrderResponseSchema
)


router = APIRouter(prefix="/order")


@router.post("/create")
async def create_order(
    order_service: OrderServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await order_service.create_order(uuid_user)


@router.patch("/update_status_order")
async def lock_update_status_order(
    order_service: OrderServiceDep,
    data: OrderStatusUpdateSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_order(data)


@router.patch("/update_status_payment")
async def lock_update_status_payment(
    order_service: OrderServiceDep,
    data: PaymentStatusUpdateSchema,
    payload = Depends(is_admin_token)
) -> None:
    await order_service.update_status_payment(data)


@router.post("/pay_order/{id_order}")
async def pay_for_order(
    order_service: OrderServiceDep,
    id_order: int,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await order_service.pay_for_order(uuid_user=uuid_user, id_order=id_order)


@router.get("/list")
async def lock_get_all_orders(
    order_service: OrderServiceDep,
    pagination: PaginationSchema = Depends(),
    payload = Depends(is_admin_token)
) -> list[OrderResponseSchema]:
    return await order_service.get_all_orders(pagination)
