import json
import aio_pika
from core_app.logger import logger


class OrderRabbitService:
    async def handle_created(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        data = json.loads(message.body)
        logger.info("received: %s", data)
        print(data)