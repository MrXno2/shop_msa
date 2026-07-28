from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core_app.db_utils import make_test_database_url
from core_app.settings import settings
from srv_catalog.src.db.models.category import CategoryORM
from srv_catalog.src.db.models.product import ProductORM
from srv_catalog.src.rabbit.services import RabbitCatalogOrderService

TEST_DATABASE_URL = make_test_database_url(
    settings.POSTGRES_URL_SERV_CATALOG, "shop_catalog_test"
)


def _make_message(data: dict) -> MagicMock:
    import json

    message = MagicMock()
    message.body = json.dumps(data, default=str).encode()
    return message


async def _seed_product(
    db: AsyncSession,
    name="Test Product",
    price="100.00",
    sale=None,
    stock=10,
) -> tuple[str, str]:
    category = CategoryORM(name=f"Cat {uuid4().hex[:8]}", description="desc")
    db.add(category)
    await db.flush()

    product = ProductORM(
        name=name,
        description="desc",
        price=price,
        sale=sale,
        stock=stock,
        category_id=category.uuid,
    )
    db.add(product)
    await db.commit()
    return str(product.uuid), str(category.uuid)


async def _verify_product(product_uuid: str, **expected_attrs):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        result = await session.execute(
            select(ProductORM).where(ProductORM.uuid == product_uuid)
        )
        product = result.scalar_one()
        for attr, value in expected_attrs.items():
            actual = getattr(product, attr)
            assert actual == value, f"{attr}: expected {value}, got {actual}"
    await engine.dispose()


class FakeSessionFactory:
    def __init__(self, db):
        self._db = db

    def __call__(self):
        return self._CM(self._db)

    class _CM:
        def __init__(self, db):
            self._db = db

        async def __aenter__(self):
            return self._db

        async def __aexit__(self, *args):
            pass


class TestDeductFromStockSuccess:
    @pytest.mark.asyncio
    async def test_stock_is_reduced(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=10)
        data = {
            "id_order": 1,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 3,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(product_uuid, stock=7)

    @pytest.mark.asyncio
    async def test_multiple_products_all_deducted(self, db_session: AsyncSession):
        p1_uuid, _ = await _seed_product(db_session, name="P1", stock=10, price="100.00", sale=None)
        p2_uuid, _ = await _seed_product(db_session, name="P2", stock=20, price="50.00", sale=None)

        seed_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with async_sessionmaker(seed_engine, class_=AsyncSession)() as verify_session:
            r1 = await verify_session.execute(select(ProductORM).where(ProductORM.uuid == p1_uuid))
            r2 = await verify_session.execute(select(ProductORM).where(ProductORM.uuid == p2_uuid))
            assert r1.scalar_one().stock == 10
            assert r2.scalar_one().stock == 20
        await seed_engine.dispose()

        data = {
            "id_order": 2,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": p1_uuid,
                    "name": "P1",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 4,
                },
                {
                    "uuid": p2_uuid,
                    "name": "P2",
                    "price": "50.00",
                    "sale": None,
                    "count_product": 5,
                },
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(p1_uuid, stock=6)
        await _verify_product(p2_uuid, stock=15)

    @pytest.mark.asyncio
    async def test_publishes_created_status(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=10)
        user_uuid = uuid4()
        data = {
            "id_order": 7,
            "uuid_user": str(user_uuid),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 2,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        mock_rabbit.publish.assert_awaited_once()
        call_args = mock_rabbit.publish.call_args
        assert call_args.args[0] == "catalog_order.handle_stock_deduction_result"
        payload = call_args.args[1]
        assert payload["id_order"] == 7
        assert payload["uuid_user"] == str(user_uuid)
        assert payload["status_order_type"] == "created"


class TestDeductFromStockInsufficientStock:
    @pytest.mark.asyncio
    async def test_insufficient_stock_rollback_and_cancel(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=2)
        data = {
            "id_order": 3,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 5,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(product_uuid, stock=2)

        call_args = mock_rabbit.publish.call_args
        payload = call_args.args[1]
        assert payload["status_order_type"] == "cancelled"

    @pytest.mark.asyncio
    async def test_insufficient_stock_does_not_commit(self, db_session: AsyncSession):
        p1_uuid, _ = await _seed_product(db_session, name="P1", stock=1)
        p2_uuid, _ = await _seed_product(db_session, name="P2", stock=100)
        data = {
            "id_order": 4,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": p1_uuid,
                    "name": "P1",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 10,
                },
                {
                    "uuid": p2_uuid,
                    "name": "P2",
                    "price": "50.00",
                    "sale": None,
                    "count_product": 1,
                },
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(p1_uuid, stock=1)
        await _verify_product(p2_uuid, stock=100)


class TestDeductFromStockPriceMismatch:
    @pytest.mark.asyncio
    async def test_price_mismatch_rollback_and_cancel(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=10, price="100.00")
        data = {
            "id_order": 5,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "200.00",
                    "sale": None,
                    "count_product": 1,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(product_uuid, stock=10)

        call_args = mock_rabbit.publish.call_args
        payload = call_args.args[1]
        assert payload["status_order_type"] == "cancelled"

    @pytest.mark.asyncio
    async def test_sale_mismatch_rollback_and_cancel(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=10, price="100.00", sale="20.00")
        data = {
            "id_order": 6,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "100.00",
                    "sale": "50.00",
                    "count_product": 1,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(product_uuid, stock=10)

        call_args = mock_rabbit.publish.call_args
        payload = call_args.args[1]
        assert payload["status_order_type"] == "cancelled"


class TestDeductFromStockNonexistentProduct:
    @pytest.mark.asyncio
    async def test_nonexistent_product_rollback_and_cancel(self, db_session: AsyncSession):
        data = {
            "id_order": 8,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": str(uuid4()),
                    "name": "Ghost Product",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 1,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        call_args = mock_rabbit.publish.call_args
        payload = call_args.args[1]
        assert payload["status_order_type"] == "cancelled"


class TestDeductFromStockExactlyEnoughStock:
    @pytest.mark.asyncio
    async def test_exact_stock_deducts_to_zero(self, db_session: AsyncSession):
        product_uuid, _ = await _seed_product(db_session, stock=5)
        data = {
            "id_order": 9,
            "uuid_user": str(uuid4()),
            "products": [
                {
                    "uuid": product_uuid,
                    "name": "Test Product",
                    "price": "100.00",
                    "sale": None,
                    "count_product": 5,
                }
            ],
        }
        message = _make_message(data)

        mock_rabbit = MagicMock()
        mock_rabbit.publish = AsyncMock()

        with (
            patch("srv_catalog.src.rabbit.services.db_session", FakeSessionFactory(db_session)),
            patch("srv_catalog.src.rabbit.services.rabbit_catalog_order", mock_rabbit),
        ):
            service = RabbitCatalogOrderService()
            await service.deduct_from_stock(message)

        await _verify_product(product_uuid, stock=0)

        call_args = mock_rabbit.publish.call_args
        payload = call_args.args[1]
        assert payload["status_order_type"] == "created"
