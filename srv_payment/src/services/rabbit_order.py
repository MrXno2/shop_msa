import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession
from srv_payment.src.db.session import db_session


class RabbitOrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wallet(self):
        ...

    async def debit_wallet(self):
        ...


class RabbitOrderService:
    async def payment_order(
        self,
        message: aio_pika.IncomingMessage
    ):
        async with db_session() as db:
            # тут выполняем списание и проброс в корзину об успешной оплате
            ...