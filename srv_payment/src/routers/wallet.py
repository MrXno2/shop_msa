# тут должно быть пополнение счета юзера, сделали ручку для имитации


from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core_app.security import is_admin_token, is_validity_token
from srv_payment.src.db.models.wallet import WalletORM
from srv_payment.src.dependensies import DbDep
from srv_payment.src.services.rabbit_payment_order import WalletRepository


router = APIRouter(prefix="/payment")


class DepositWalletSchema(BaseModel):
    uuid_user: UUID
    dep_price: Decimal


class WalletService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)

    async def deposit_balance(self, data_req: DepositWalletSchema):
        result = await self.wallet_repo.deposit_wallet(
            uuid_user=data_req.uuid_user,
            deposit_price=data_req.dep_price
        )
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not Found in wallet service")
        await self.db.commit()

    async def get_wallet(self, uuid_user: UUID) -> Decimal:
        wallet = await self.wallet_repo.get_wallet(uuid_user)
        if wallet is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wallet not found")
        return wallet.balance


async def get_wallet_service(db: DbDep) -> WalletService:
    return WalletService(db)

WalletServiceDep = Annotated[WalletService, Depends(get_wallet_service)]


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