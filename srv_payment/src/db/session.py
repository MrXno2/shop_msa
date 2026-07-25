from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core_app.settings import settings


engine = create_async_engine(settings.POSTGRES_URL_SERV_PAYMENT)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session