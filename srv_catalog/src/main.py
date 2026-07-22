from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from core_app.middleware import set_cors
from srv_catalog.src.rabbit.rabbit import rabbit_catalog_order
from srv_catalog.src.db.models.base import Base
from srv_catalog.src.routers.product import router as routers_auth
from core_app.exception_handler import register_exception_handlers
from srv_catalog.src.db.session import engine
from core_app.logger import logger


# register_consumers_cart_product_cache(rabbit_orders)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await rabbit_catalog_order.start()

    logger.warning("START service CATALOG")

    yield

    await rabbit_catalog_order.stop()

    logger.warning("STOP service CATALOG")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_auth)
