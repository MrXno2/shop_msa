from contextlib import asynccontextmanager

from fastapi import FastAPI

from core_app.exception_handler import register_exception_handlers
from core_app.logger import logger
from core_app.middleware import set_cors
from core_app.rabbit import rabbit_payment_auth
from srv_auth.src.modules.auth.routers import router as routers_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbit_payment_auth.start()
    logger.warning("START service AUTH")
    yield
    await rabbit_payment_auth.stop()
    logger.warning("STOP service AUTH")


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_auth)


@app.get("/health")
async def health():
    return {"status": "ok"}
