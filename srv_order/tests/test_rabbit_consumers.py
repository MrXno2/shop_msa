from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.enums import OrderStatusEnum
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.cart_user import CartORM
from srv_order.src.db.models.order import OrderORM
from srv_order.src.rabbit.services import RabbitCatalogOrderService, RabbitPaymentOrderService


def _make_message(data: dict) -> MagicMock:
    message = MagicMock()
    message.body = __import__("pydantic").BaseModel.model_dump_json(
        __import__("pydantic").BaseModel, data
    ).encode() if False else b""
    import json
    message.body = json.dumps(data, default=str).encode()
    return message


class TestCreateProduct:
    @pytest.mark.asyncio
    async def test_creates_cache_record(self, db_session: AsyncSession):
        product_uuid = uuid4()
        data = {
            "uuid": str(product_uuid),
            "name": "Laptop",
            "price": "999.99",
            "sale": "100.00",
            "image_url": "http://img.jpg",
        }
        message = _make_message(data)

        service = RabbitCatalogOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            await service.create_product(message)

        result = await db_session.execute(
            select(CartProductCacheORM).where(CartProductCacheORM.uuid_product == product_uuid)
        )
        product = result.scalar_one()
        assert product.name == "Laptop"
        assert product.price == Decimal("999.99")

    @pytest.mark.asyncio
    async def test_idempotent_on_duplicate(self, db_session: AsyncSession):
        product_uuid = uuid4()
        existing = CartProductCacheORM(
            uuid_product=product_uuid, name="Existing", price="10.00"
        )
        db_session.add(existing)
        await db_session.flush()
        await db_session.commit()
        db_session.expunge(existing)

        data = {
            "uuid": str(product_uuid),
            "name": "Duplicate",
            "price": "20.00",
        }
        message = _make_message(data)

        service = RabbitCatalogOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            await service.create_product(message)

        result = await db_session.execute(
            select(CartProductCacheORM).where(CartProductCacheORM.uuid_product == product_uuid)
        )
        product = result.scalar_one()
        assert product.name == "Existing"


class TestDelProduct:
    @pytest.mark.asyncio
    async def test_deletes_cache_record(self, db_session: AsyncSession):
        product_uuid = uuid4()
        product = CartProductCacheORM(
            uuid_product=product_uuid, name="To Delete", price="10.00"
        )
        db_session.add(product)
        await db_session.flush()

        message = _make_message({"uuid_product": str(product_uuid)})
        service = RabbitCatalogOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            await service.del_product(message)

        result = await db_session.execute(
            select(CartProductCacheORM).where(CartProductCacheORM.uuid_product == product_uuid)
        )
        assert result.scalar_one_or_none() is None


class TestFullUpdateProduct:
    @pytest.mark.asyncio
    async def test_updates_cache_record(self, db_session: AsyncSession):
        product_uuid = uuid4()
        product = CartProductCacheORM(
            uuid_product=product_uuid, name="Old Name", price="10.00"
        )
        db_session.add(product)
        await db_session.flush()

        data = {
            "uuid": str(product_uuid),
            "name": "New Name",
            "price": "20.00",
        }
        message = _make_message(data)
        service = RabbitCatalogOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            await service.full_update_product(message)

        await db_session.refresh(product)
        assert product.name == "New Name"
        assert product.price == 20.00

    @pytest.mark.asyncio
    async def test_product_not_found(self, db_session: AsyncSession):
        data = {
            "uuid": str(uuid4()),
            "name": "Ghost",
            "price": "10.00",
        }
        message = _make_message(data)
        service = RabbitCatalogOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        from core_app.exception import ProductNotFound

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            with pytest.raises(ProductNotFound):
                await service.full_update_product(message)


class TestHandleStockDeductionResult:
    @pytest.mark.asyncio
    async def test_created_clears_cart_and_updates_order(self, db_session: AsyncSession):
        user_uuid = uuid4()

        order = OrderORM(
            uuid_user=user_uuid,
            status_order=OrderStatusEnum.PENDING,
            total_price="100.00",
            items=[],
        )
        db_session.add(order)
        await db_session.flush()

        product_uuid = uuid4()
        product = CartProductCacheORM(uuid_product=product_uuid, name="P", price="10.00")
        db_session.add(product)
        cart = CartORM(uuid_user=user_uuid, uuid_product=product_uuid, count_product=1)
        db_session.add(cart)
        await db_session.flush()

        data = {
            "id_order": order.id,
            "uuid_user": str(user_uuid),
            "status_order_type": "created",
        }
        message = _make_message(data)
        service = RabbitCatalogOrderService()

        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with (
            patch("srv_order.src.rabbit.services.db_session", FakeSession),
            patch("srv_order.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.handle_stock_deduction_result(message)

        await db_session.refresh(order)
        assert order.status_order == OrderStatusEnum.CREATED

        result = await db_session.execute(
            select(CartORM).where(CartORM.uuid_user == user_uuid)
        )
        assert result.scalar_one_or_none() is None

        mock_notif.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancelled_does_not_clear_cart(self, db_session: AsyncSession):
        user_uuid = uuid4()

        order = OrderORM(
            uuid_user=user_uuid,
            status_order=OrderStatusEnum.PENDING,
            total_price="100.00",
            items=[],
        )
        db_session.add(order)
        await db_session.flush()

        product_uuid = uuid4()
        product = CartProductCacheORM(uuid_product=product_uuid, name="P", price="10.00")
        db_session.add(product)
        cart = CartORM(uuid_user=user_uuid, uuid_product=product_uuid, count_product=1)
        db_session.add(cart)
        await db_session.flush()

        data = {
            "id_order": order.id,
            "uuid_user": str(user_uuid),
            "status_order_type": "cancelled",
        }
        message = _make_message(data)
        service = RabbitCatalogOrderService()

        mock_notif = MagicMock()
        mock_notif.publish = AsyncMock()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with (
            patch("srv_order.src.rabbit.services.db_session", FakeSession),
            patch("srv_order.src.rabbit.services.rabbit_all_notification", mock_notif),
        ):
            await service.handle_stock_deduction_result(message)

        await db_session.refresh(order)
        assert order.status_order == OrderStatusEnum.CANCELLED

        result = await db_session.execute(
            select(CartORM).where(CartORM.uuid_user == user_uuid)
        )
        assert result.scalar_one() is not None


class TestPaymentOrderServiceUpdateStatusPayment:
    @pytest.mark.asyncio
    async def test_updates_payment_status(self, db_session: AsyncSession):
        user_uuid = uuid4()
        order = OrderORM(
            uuid_user=user_uuid,
            status_order=OrderStatusEnum.CREATED,
            status_payment=False,
            total_price="100.00",
            items=[],
        )
        db_session.add(order)
        await db_session.flush()

        data = {
            "uuid_user": str(user_uuid),
            "id_order": order.id,
            "payment_success": True,
        }
        message = _make_message(data)
        service = RabbitPaymentOrderService()

        class FakeSession:
            async def __aenter__(self):
                return db_session
            async def __aexit__(self, *args):
                pass

        with patch("srv_order.src.rabbit.services.db_session", FakeSession):
            await service.update_status_payment(message)

        await db_session.refresh(order)
        assert order.status_payment is True
