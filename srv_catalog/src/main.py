from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from core_app.middleware import set_cors
from srv_catalog.src.rabbit.reg_consum import register_consumers_cart_product_cache
from srv_catalog.src.rabbit.rabbit import rabbit_cart_product_cache
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

    await rabbit_cart_product_cache.start()

    logger.warning("START service CATALOG")

    yield

    await rabbit_cart_product_cache.stop()

    logger.warning("STOP service CATALOG")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_auth)


# пример
class Order(BaseModel):
    user_id: int
    product: str
    
@app.post("/orders")
async def create_order(order: Order):
    await rabbit_cart_product_cache.publish("order.created", {"user_id": order.user_id, "product": order.product})
    return {"status": "ok"}