import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import aio_pika

from core_app.logger import logger
from core_app.settings import settings


Handler = Callable[[aio_pika.IncomingMessage], Awaitable[None]]


@dataclass(slots=True)
class Consumer:
    queue: str
    routing_key: str
    handler: Handler
    durable: bool = True


class RabbitMain:
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name

        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

        self._registered: list[Consumer] = []
        self._tasks: list[asyncio.Task[None]] = []


    def consumer(
        self,
        *,
        queue: str,
        routing_key: str,
        handler: Handler,
        durable: bool = True,
    ) -> None:
        """Регистрирует consumer. Ничего не запускает."""
        self._registered.append(
            Consumer(
                queue=queue,
                routing_key=routing_key,
                handler=handler,
                durable=durable,
            )
        )


    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.RABBIT_URL)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._exchange = await self._channel.declare_exchange(
            self.exchange_name,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )
        for consumer in self._registered:
            task = asyncio.create_task(
                self._run_consumer(consumer)
            )
            self._tasks.append(task)


    async def publish(
        self,
        routing_key: str,
        data: dict,
    ) -> None:
        if self._exchange is None:
            raise RuntimeError("Rabbit is not started")
        await self._exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )


    async def _run_consumer(
        self,
        consumer: Consumer,
    ) -> None:
        if self._channel is None:
            raise RuntimeError("Rabbit is not started")
        queue = await self._channel.declare_queue(
            consumer.queue,
            durable=consumer.durable,
        )
        if self._exchange is None:
            raise RuntimeError("Rabbit is not started")
        await queue.bind(
            self._exchange,
            routing_key=consumer.routing_key,
        )
        async with queue.iterator() as iterator:
            async for message in iterator:
                try:
                    await consumer.handler(message) #type: ignore
                    await message.ack()
                except asyncio.CancelledError:
                    await message.nack(requeue=False)
                    raise
                except Exception:
                    await message.nack(requeue=True)
                    logger.exception("handler failed")


    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(
            *self._tasks,
            return_exceptions=True,
        )

        if self._connection:
            await self._connection.close()

rabbit_wallet_user = RabbitMain(exchange_name="payment_auth")

rabbit_payment_order = RabbitMain(exchange_name="payment_order")