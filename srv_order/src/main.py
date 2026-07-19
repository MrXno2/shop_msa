from contextlib import asynccontextmanager
from fastapi import FastAPI
from core_app.middleware import set_cors
from srv_order.src.db.models.base import Base
from srv_order.src.routers.cart import router as routers_cart
from core_app.exception_handler import register_exception_handlers
from srv_order.src.db.session import engine
from core_app.logger import logger
from srv_order.src.rabbit.rabbit import rabbit_cart_product_cache
from srv_order.src.rabbit.reg_consum import register_consumers_cart_product_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await register_consumers_cart_product_cache(rabbit_cart_product_cache)

    await rabbit_cart_product_cache.start()

    logger.warning("START service ORDER")
    yield

    await rabbit_cart_product_cache.stop()

    logger.warning("STOP service ORDER")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_cart)