import aio_pika
from pydantic import ValidationError
from srv_payment.src.db.session import db_session
from srv_payment.src.modules.wallet.repository import WalletRepository
from srv_payment.src.rabbit.schemas import RabbitRequestOrderPaymentSchema, RabbitResponseOrderPaymentSchema, RabbitWalletUserSchema
from core_app.rabbit import rabbit_payment_order
from core_app.logger import logger
from sqlalchemy.exc import SQLAlchemyError


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