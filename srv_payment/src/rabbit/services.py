import aio_pika
from pydantic import ValidationError
from srv_payment.src.db.models.history_wallet import HistoryWalletORM
from srv_payment.src.db.session import db_session
from srv_payment.src.modules.history_wallet.repository import HistoryWalletRepository
from srv_payment.src.modules.wallet.repository import WalletRepository
from srv_payment.src.rabbit.schemas import RabbitAddNotificationSchema, RabbitRequestOrderPaymentSchema, RabbitResponseOrderPaymentSchema, RabbitWalletUserSchema
from core_app.rabbit import rabbit_payment_order, rabbit_all_notification
from core_app.logger import logger
from sqlalchemy.exc import SQLAlchemyError
from core_app.messages_notification import messages


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
                history_wallet_repo = HistoryWalletRepository(db)
                data_req = RabbitRequestOrderPaymentSchema.model_validate_json(message.body)
                result = await wallet_repo.debit_wallet(uuid_user=data_req.uuid_user, debit_price=data_req.total_price)
                data_response = RabbitResponseOrderPaymentSchema(
                    uuid_user=data_req.uuid_user,
                    id_order=data_req.id_order,
                    payment_success=True
                )
                notif = RabbitAddNotificationSchema(
                    uuid_user=data_response.uuid_user,
                    title_notification=f"{messages.NAME_ORDER} {data_response.id_order}",
                    message_notification=messages.DESC_ORDER_PAYMENT_TRUE
                )
                if result is None:
                    data_response.payment_success = False
                    notif.message_notification = messages.DESC_ORDER_PAYMENT_FALSE
                else:
                    history_wallet_orm = HistoryWalletORM(
                        uuid_user = data_req.uuid_user,
                        transaction_type = "payment",
                        amount = data_req.total_price
                    )
                    history_wallet_repo.add_history_wallet(history_wallet_orm)
                    await db.commit()
                await rabbit_payment_order.publish(
                    "payment_order.update_status_payment", 
                    data_response.model_dump(mode="json")
                )
                await rabbit_all_notification.publish(
                    "all_notification.add", 
                    notif.model_dump(mode='json')
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