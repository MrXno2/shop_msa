from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core_app.db_utils import ensure_test_database, make_test_database_url
from srv_payment.src.db.models.base import Base
from srv_payment.src.db.session import get_db
from srv_payment.src.main import app

from core_app.settings import settings

TEST_DATABASE_URL = make_test_database_url(
    settings.POSTGRES_URL_SERV_PAYMENT, "shop_payment_test"
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    await ensure_test_database(TEST_DATABASE_URL)
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()

    yield session

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    await session.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_auth = MagicMock()
    mock_auth.start = AsyncMock()
    mock_auth.stop = AsyncMock()
    mock_auth.consumer = MagicMock()

    mock_order = MagicMock()
    mock_order.start = AsyncMock()
    mock_order.stop = AsyncMock()
    mock_order.consumer = MagicMock()
    mock_order.publish = AsyncMock()

    mock_notif = MagicMock()
    mock_notif.publish = AsyncMock()

    with (
        patch("srv_payment.src.main.rabbit_payment_auth", mock_auth),
        patch("srv_payment.src.main.rabbit_payment_order", mock_order),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
