from decimal import Decimal
import json
from uuid import UUID
from xml.dom.pulldom import parseString
from core_app.rabbit import rabbit_payment_order
import aio_pika
from pydantic import BaseModel, ValidationError
from sqlalchemy import select, update
from core_app.logger import logger
from core_app.exception import InsufficientFundsError
from srv_payment.src.db.models.wallet import WalletORM
from srv_payment.src.db.session import db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class RabbitWalletUserSchema(BaseModel):
    uuid_user: UUID
    number: str


class RabbitRequestOrderPaymentSchema(BaseModel):
    uuid_user: UUID
    id_order: int
    total_price: Decimal


class RabbitResponseOrderPaymentSchema(BaseModel):
    id_order: int
    payment_success: bool
    error_message: str | None = None


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


class RabbitPaymentAuthService():
    async def create_user(
        self,
        message: aio_pika.IncomingMessage
    ):
        async with db_session() as db:
            wallet_repo = WalletRepository(db)
            data = RabbitWalletUserSchema.model_validate_json(message.body)
            await wallet_repo.create_user(data)
            await db.commit()


class RabbitPaymentOrderService:
    async def payment_order(
        self,
        message: aio_pika.IncomingMessage
    ):
        async with db_session() as db:
            try:
                wallet_repo = WalletRepository(db)
                data_req = RabbitRequestOrderPaymentSchema.model_validate_json(message.body)
                result = await wallet_repo.debit_wallet(uuid_user=data_req.uuid_user, debit_price=data_req.total_price)
                data_response = RabbitResponseOrderPaymentSchema(
                    id_order=data_req.id_order,
                    payment_success=True
                )
                if result is None:
                    data_response.payment_success = False
                else:
                    await db.commit()
                await rabbit_payment_order.publish(
                    "payment_order.update_status_payment", 
                    data_response.model_dump(mode="json")
                )
            except ValidationError as e:
                logger.critical(
                    f"INVALID MESSAGE SCHEMA: {e}, "
                    f"body: {message.body[:200]}"
                )
                return
                
            except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                await db.rollback()
                raise 
                
            except Exception as e:
                logger.exception(
                    f"Unexpected error: {e}, "
                    f"data: {message.body[:200]}"
                )
                await db.rollback()