from contextlib import asynccontextmanager
from fastapi import FastAPI
from core_app.middleware import set_cors
from srv_payment.src.db.models.base import Base
from core_app.exception_handler import register_exception_handlers
from srv_payment.src.db.session import engine
from core_app.logger import logger
from core_app.rabbit import rabbit_payment_order, rabbit_payment_auth
from srv_payment.src.rabbit.reg_consum import register_consumers_payment_order, register_consumers_payment_auth
from srv_payment.src.modules.wallet.routers import router as router_dep


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

app.include_router(router_dep)

@app.get("/health")
async def health():
    return {"status": "ok"}