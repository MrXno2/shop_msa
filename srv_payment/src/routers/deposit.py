# тут должно быть пополнение счета юзера, сделали ручку для имитации


from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from shop_msa.core_app.security import is_admin_token
from shop_msa.srv_payment.src.dependensies import DbDep
from shop_msa.srv_payment.src.services.rabbit_payment_order import WalletRepository


router = APIRouter(prefix="/payment")


class DepositeWalletSchema(BaseModel):
    uuid_user: UUID
    dep_price: Decimal


class WalletService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)

    async def deposit_balance(self, data_req: DepositeWalletSchema):
        await self.wallet_repo.deposit_wallet(
            uuid_user=data_req.uuid_user,
            deposit_price=data_req.dep_price
        )
        await self.db.commit()


async def get_wallet_service(db: DbDep) -> WalletService:
    return WalletService(db)

WalletServiceDep = Annotated[WalletService, Depends(get_wallet_service)]


@router.post("/deposit")
async def deposit_balance_user(
    wallet_service: WalletServiceDep,
    data_req: DepositeWalletSchema,
    payload = Depends(is_admin_token)
) -> None:
    await wallet_service.deposit_balance(data_req)