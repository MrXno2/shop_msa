from contextlib import asynccontextmanager
from fastapi import FastAPI
from core_app.middleware import set_cors
from srv_auth.src.db.models.base import Base
from srv_auth.src.routers.auth import router as routers_auth
from core_app.exception_handler import register_exception_handlers
from srv_auth.src.db.session import engine
from core_app.logger import logger
from core_app.rabbit import rabbit_payment_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await rabbit_payment_auth.start()      
    logger.warning("START service AUTH")
    yield
    await rabbit_payment_auth.stop() 
    logger.warning("STOP service AUTH")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_auth)