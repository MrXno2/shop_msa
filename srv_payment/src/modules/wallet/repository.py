from decimal import Decimal
from uuid import UUID
from sqlalchemy import select, update
from srv_payment.src.db.models.wallet import WalletORM
from sqlalchemy.ext.asyncio import AsyncSession
from srv_payment.src.rabbit.schemas import RabbitWalletUserSchema


class WalletRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, data: RabbitWalletUserSchema):
        data_wallet = WalletORM(
            uuid_user = data.uuid_user,
            number = data.number,
            balance = Decimal('0.00')
        )
        self.db.add(data_wallet)

    async def get_wallet(self, uuid_user: UUID) -> WalletORM | None:
        result = await self.db.execute(
            select(WalletORM)
            .where(WalletORM.uuid_user == uuid_user)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def debit_wallet(
        self, 
        uuid_user: UUID,
        debit_price: Decimal
    ) -> WalletORM | None:
        result = await self.db.execute(
            update(WalletORM)
            .where(
                WalletORM.uuid_user == uuid_user,
                WalletORM.balance >= debit_price
            )
            .values(balance = WalletORM.balance - debit_price)
            .returning(WalletORM)
        )
        return result.scalar_one_or_none()
    
    async def deposit_wallet(
        self,
        uuid_user: UUID,
        deposit_price: Decimal
    ) -> WalletORM | None:
        result = await self.db.execute(
            update(WalletORM)
            .where(WalletORM.uuid_user == uuid_user)
            .values(balance = WalletORM.balance + deposit_price)
            .returning(WalletORM)
        )
        return result.scalar_one_or_none()