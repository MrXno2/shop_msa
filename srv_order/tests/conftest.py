import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core_app.db_utils import ensure_test_database, make_test_database_url
from srv_order.src.db.models.base import Base
from srv_order.src.db.session import get_db
from srv_order.src.main import app

from core_app.settings import settings

TEST_DATABASE_URL = make_test_database_url(
    settings.POSTGRES_URL_SERV_ORDER, "shop_order_test"
)


@pytest.fixture
def mock_catalog_publish():
    mock = MagicMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.consumer = MagicMock()
    mock.publish = AsyncMock()
    return mock


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
async def client(db_session: AsyncSession, mock_catalog_publish: MagicMock) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_catalog = mock_catalog_publish

    mock_payment = MagicMock()
    mock_payment.start = AsyncMock()
    mock_payment.stop = AsyncMock()
    mock_payment.consumer = MagicMock()
    mock_payment.publish = AsyncMock()

    mock_notif = MagicMock()
    mock_notif.publish = AsyncMock()

    with (
        patch("srv_order.src.main.rabbit_catalog_order", mock_catalog),
        patch("srv_order.src.main.rabbit_payment_order", mock_payment),
        patch("srv_order.src.modules.order.service.rabbit_all_notification", mock_notif),
        patch("srv_order.src.modules.order.service.rabbit_payment_order", mock_payment),
        patch("srv_order.src.modules.order.service.rabbit_catalog_order", mock_catalog),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()
