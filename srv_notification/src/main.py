from contextlib import asynccontextmanager

from fastapi import FastAPI
from srv_notification.src.modules.notification.routers import (
    router as router_notification,
)
from srv_notification.src.rabbit.reg_consum import register_consumers_all_notification

from core_app.exception_handler import register_exception_handlers
from core_app.logger import logger
from core_app.middleware import set_cors
from core_app.rabbit import rabbit_all_notification


@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_consumers_all_notification(rabbit_all_notification)

    await rabbit_all_notification.start()

    logger.warning("START service NOTIFICATION")

    yield

    await rabbit_all_notification.stop()

    logger.warning("STOP service NOTIFICATION")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(router_notification)


@app.get("/health")
async def health():
    return {"status": "ok"}
