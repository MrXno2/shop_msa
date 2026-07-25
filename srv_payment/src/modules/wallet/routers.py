from decimal import Decimal
from fastapi import APIRouter, Depends
from core_app.security import is_admin_token, is_validity_token
from srv_payment.src.dependensies import WalletServiceDep
from srv_payment.src.modules.wallet.schemas import DepositWalletSchema


router = APIRouter(prefix="/payment")


@router.post("/deposit")
async def lock_deposit_balance_user(
    wallet_service: WalletServiceDep,
    data_req: DepositWalletSchema,
    payload = Depends(is_admin_token)
) -> None:
    await wallet_service.deposit_balance(data_req)


@router.get("/balance")
async def get_balance(
    wallet_service: WalletServiceDep,
    payload = Depends(is_validity_token)
) -> Decimal:
    uuid_user = payload.get("uuid")
    return await wallet_service.get_wallet(uuid_user)