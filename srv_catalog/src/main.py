from contextlib import asynccontextmanager

from fastapi import FastAPI
from srv_catalog.src.modules.category.routers import router as router_categoty
from srv_catalog.src.modules.product.routers import router as routers_product
from srv_catalog.src.rabbit.reg_consum import register_consumers_catalog_order

from core_app.exception_handler import register_exception_handlers
from core_app.logger import logger
from core_app.middleware import set_cors
from core_app.rabbit import rabbit_catalog_order

# register_consumers_cart_product_cache(rabbit_orders)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await register_consumers_catalog_order(rabbit_catalog_order)

    await rabbit_catalog_order.start()

    logger.warning("START service CATALOG")

    yield

    await rabbit_catalog_order.stop()

    logger.warning("STOP service CATALOG")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_product)
app.include_router(router_categoty)


@app.get("/health")
async def health():
    return {"status": "ok"}
