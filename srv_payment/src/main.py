from contextlib import asynccontextmanager

from fastapi import FastAPI
from srv_payment.src.modules.wallet.routers import router as router_wallet
from srv_payment.src.rabbit.reg_consum import (
    register_consumers_payment_auth,
    register_consumers_payment_order,
)

from core_app.exception_handler import register_exception_handlers
from core_app.logger import logger
from core_app.middleware import set_cors
from core_app.rabbit import rabbit_payment_auth, rabbit_payment_order


@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_consumers_payment_order(rabbit_payment_order)
    await register_consumers_payment_auth(rabbit_payment_auth)

    await rabbit_payment_auth.start()
    await rabbit_payment_order.start()
    logger.warning("START service PAYMENT")

    yield

    await rabbit_payment_auth.stop()
    await rabbit_payment_order.stop()
    logger.warning("STOP service PAYMENT")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(router_wallet)


@app.get("/health")
async def health():
    return {"status": "ok"}
