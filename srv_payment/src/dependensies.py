from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from srv_payment.src.db.session import get_db
from srv_payment.src.modules.wallet.service import WalletService


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_wallet_service(db: DbDep) -> WalletService:
    return WalletService(db)

WalletServiceDep = Annotated[WalletService, Depends(get_wallet_service)]
