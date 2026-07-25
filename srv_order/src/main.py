from contextlib import asynccontextmanager
from fastapi import FastAPI
from core_app.middleware import set_cors
from srv_order.src.db.models.base import Base
from srv_order.src.modules.cart.routers import router as routers_cart
from srv_order.src.modules.order.routers import router as routers_order
from core_app.exception_handler import register_exception_handlers
from srv_order.src.db.session import engine
from core_app.logger import logger
from core_app.rabbit import rabbit_catalog_order, rabbit_payment_order
from srv_order.src.rabbit.reg_consum import register_consumers_catalog_order, register_consumers_payment_order


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await register_consumers_catalog_order(rabbit_catalog_order)
    await register_consumers_payment_order(rabbit_payment_order)

    await rabbit_catalog_order.start()
    await rabbit_payment_order.start()
    logger.warning("START service ORDER")
    
    yield

    await rabbit_catalog_order.stop()
    await rabbit_payment_order.stop()
    logger.warning("STOP service ORDER")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_cart)
app.include_router(routers_order)

@app.get("/health")
async def health():
    return {"status": "ok"}