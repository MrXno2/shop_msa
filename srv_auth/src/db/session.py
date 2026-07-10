from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core_app.settings import settings


engine = create_async_engine(settings.POSTGRES_URL_SERV_AUTH)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session