from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.cart_user import CartORM
from srv_order.src.db.models.order import OrderORM
from srv_order.src.modules.order.service import OrderService


def _mock_cart_repo(products):
    repo = MagicMock()
    repo.get_all_product = AsyncMock(return_value=products)
    return repo


def _mock_order_repo(order=None):
    repo = MagicMock()
    repo.create_order = AsyncMock(return_value=order)
    return repo


def _make_cart_item(price, sale, count=1):
    product = MagicMock(spec=CartProductCacheORM)
    product.uuid_product = uuid4()
    product.name = "Test"
    product.price = Decimal(str(price))
    product.sale = Decimal(str(sale)) if sale is not None else None
    product.image_url = None
    cart = MagicMock(spec=CartORM)
    cart.count_product = count
    return product, cart


class TestCreateOrderPriceCalculation:
    @pytest.mark.asyncio
    async def test_single_product_no_sale(self):
        db = AsyncMock(spec=AsyncSession)
        service = OrderService(db)

        product, cart = _make_cart_item("100.00", "0.00", count=3)
        service.cart_repo = _mock_cart_repo([(product, cart)])

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.items = []
        service.order_repo = _mock_order_repo(mock_order)

        mock_catalog = MagicMock()
        mock_catalog.publish = AsyncMock()
        mock_payment = MagicMock()
        mock_payment.publish = AsyncMock()

        with (
            patch("srv_order.src.modules.order.service.rabbit_catalog_order", mock_catalog),
            patch("srv_order.src.modules.order.service.rabbit_payment_order", mock_payment),
        ):
            await service.create_order(uuid_user=uuid4())

        call_args = service.order_repo.create_order.call_args
        order: OrderORM = call_args[0][0]
        assert order.total_price == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_single_product_with_sale(self):
        db = AsyncMock(spec=AsyncSession)
        service = OrderService(db)

        product, cart = _make_cart_item("200.00", "25.00", count=2)
        service.cart_repo = _mock_cart_repo([(product, cart)])

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.items = []
        service.order_repo = _mock_order_repo(mock_order)

        mock_catalog = MagicMock()
        mock_catalog.publish = AsyncMock()
        mock_payment = MagicMock()
        mock_payment.publish = AsyncMock()

        with (
            patch("srv_order.src.modules.order.service.rabbit_catalog_order", mock_catalog),
            patch("srv_order.src.modules.order.service.rabbit_payment_order", mock_payment),
        ):
            await service.create_order(uuid_user=uuid4())

        call_args = service.order_repo.create_order.call_args
        order: OrderORM = call_args[0][0]
        assert order.total_price == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_multiple_products_mixed(self):
        db = AsyncMock(spec=AsyncSession)
        service = OrderService(db)

        p1, c1 = _make_cart_item("100.00", "0.00", count=1)
        p2, c2 = _make_cart_item("200.00", "50.00", count=1)
        p3, c3 = _make_cart_item("50.00", "10.00", count=3)
        service.cart_repo = _mock_cart_repo([(p1, c1), (p2, c2), (p3, c3)])

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.items = []
        service.order_repo = _mock_order_repo(mock_order)

        mock_catalog = MagicMock()
        mock_catalog.publish = AsyncMock()
        mock_payment = MagicMock()
        mock_payment.publish = AsyncMock()

        with (
            patch("srv_order.src.modules.order.service.rabbit_catalog_order", mock_catalog),
            patch("srv_order.src.modules.order.service.rabbit_payment_order", mock_payment),
        ):
            await service.create_order(uuid_user=uuid4())

        call_args = service.order_repo.create_order.call_args
        order: OrderORM = call_args[0][0]
        expected = Decimal("100.00") + Decimal("100.00") + Decimal("135.00")
        assert order.total_price == expected

    @pytest.mark.asyncio
    async def test_sale_none_treated_as_zero(self):
        db = AsyncMock(spec=AsyncSession)
        service = OrderService(db)

        product, cart = _make_cart_item("100.00", None, count=2)
        service.cart_repo = _mock_cart_repo([(product, cart)])

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.items = []
        service.order_repo = _mock_order_repo(mock_order)

        mock_catalog = MagicMock()
        mock_catalog.publish = AsyncMock()
        mock_payment = MagicMock()
        mock_payment.publish = AsyncMock()

        with (
            patch("srv_order.src.modules.order.service.rabbit_catalog_order", mock_catalog),
            patch("srv_order.src.modules.order.service.rabbit_payment_order", mock_payment),
        ):
            await service.create_order(uuid_user=uuid4())

        call_args = service.order_repo.create_order.call_args
        order: OrderORM = call_args[0][0]
        assert order.total_price == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_empty_cart_raises_400(self):
        db = AsyncMock(spec=AsyncSession)
        service = OrderService(db)
        service.cart_repo = _mock_cart_repo([])

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.create_order(uuid_user=uuid4())
        assert exc_info.value.status_code == 400
