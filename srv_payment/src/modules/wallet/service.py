from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from srv_payment.src.db.models.history_wallet import HistoryWalletORM
from srv_payment.src.modules.history_wallet.repository import HistoryWalletRepository
from srv_payment.src.modules.wallet.repository import WalletRepository
from srv_payment.src.modules.wallet.schemas import DepositWalletSchema


class WalletService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)
        self.history_wallet_repo = HistoryWalletRepository(db)

    async def deposit_balance(self, data_req: DepositWalletSchema):
        result = await self.wallet_repo.deposit_wallet(uuid_user=data_req.uuid_user, deposit_price=data_req.dep_price)
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not Found in wallet service")
        history_wallet_orm = HistoryWalletORM(
            uuid_user=data_req.uuid_user,
            transaction_type="deposited",
            amount=data_req.dep_price,
        )
        self.history_wallet_repo.add_history_wallet(history_wallet_orm)
        await self.db.commit()

    async def get_wallet(self, uuid_user: UUID) -> Decimal:
        wallet = await self.wallet_repo.get_wallet(uuid_user)
        if wallet is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Wallet not found")
        return wallet.balance
