from contextlib import asynccontextmanager
from fastapi import FastAPI
from core_app.middleware import set_cors
from srv_auth.src.modules.auth.routers import router as routers_auth
from core_app.exception_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    yield


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app=app)

set_cors(app=app)

app.include_router(routers_auth)