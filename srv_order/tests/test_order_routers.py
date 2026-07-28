from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.enums import OrderStatusEnum
from core_app.security import create_access_token
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.cart_user import CartORM
from srv_order.src.db.models.order import OrderORM


def _user_headers(user_uuid=None):
    if user_uuid is None:
        user_uuid = uuid4()
    token = create_access_token({"uuid": str(user_uuid)})
    return {"Cookie": f"access_token={token}"}, user_uuid


def _admin_headers():
    token = create_access_token({"uuid": "admin"})
    return {"Cookie": f"admin_access_token={token}"}


async def _seed_product_and_cart(db: AsyncSession, user_uuid, price="100.00", sale="10.00", count=1):
    product_uuid = uuid4()
    product = CartProductCacheORM(
        uuid_product=product_uuid,
        name="Test Product",
        price=price,
        sale=sale,
        image_url="http://img.jpg",
    )
    db.add(product)
    cart = CartORM(uuid_user=user_uuid, uuid_product=product_uuid, count_product=count)
    db.add(cart)
    await db.flush()
    return product_uuid


async def _seed_order(db: AsyncSession, user_uuid, status=OrderStatusEnum.PENDING, total="100.00"):
    order = OrderORM(
        uuid_user=user_uuid,
        status_order=status,
        total_price=total,
        items=[],
    )
    db.add(order)
    await db.flush()
    return order


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        headers, user_uuid = _user_headers()
        await _seed_product_and_cart(db_session, user_uuid, price="200.00", sale="50.00", count=2)

        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 200

        result = await db_session.execute(
            select(OrderORM).where(OrderORM.uuid_user == user_uuid)
        )
        order = result.scalar_one()
        assert order is not None
        assert order.status_order == OrderStatusEnum.PENDING
        assert order.status_payment is False
        # price=200, sale=50%, count=2: 200/100*(100-50)*2 = 200.00
        assert order.total_price == Decimal("200.00")
        assert len(order.items) == 1
        assert order.items[0]["name"] == "Test Product"

    @pytest.mark.asyncio
    async def test_empty_cart_returns_400(self, client: AsyncClient):
        headers, _ = _user_headers()
        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.post("/order/create")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_price_calculation_no_sale(self, client: AsyncClient, db_session: AsyncSession):
        headers, user_uuid = _user_headers()
        await _seed_product_and_cart(db_session, user_uuid, price="100.00", sale="0.00", count=3)

        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 200

        result = await db_session.execute(
            select(OrderORM).where(OrderORM.uuid_user == user_uuid)
        )
        order = result.scalar_one()
        assert order.total_price == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_price_calculation_with_sale(self, client: AsyncClient, db_session: AsyncSession):
        headers, user_uuid = _user_headers()
        await _seed_product_and_cart(db_session, user_uuid, price="100.00", sale="20.00", count=1)

        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 200

        result = await db_session.execute(
            select(OrderORM).where(OrderORM.uuid_user == user_uuid)
        )
        order = result.scalar_one()
        assert order.total_price == Decimal("80.00")

    @pytest.mark.asyncio
    async def test_price_calculation_multiple_products(self, client: AsyncClient, db_session: AsyncSession):
        headers, user_uuid = _user_headers()

        p1_uuid = uuid4()
        db_session.add(CartProductCacheORM(uuid_product=p1_uuid, name="A", price="100.00", sale="0.00"))
        db_session.add(CartORM(uuid_user=user_uuid, uuid_product=p1_uuid, count_product=1))

        p2_uuid = uuid4()
        db_session.add(CartProductCacheORM(uuid_product=p2_uuid, name="B", price="50.00", sale="10.00"))
        db_session.add(CartORM(uuid_user=user_uuid, uuid_product=p2_uuid, count_product=2))
        await db_session.flush()

        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 200

        result = await db_session.execute(
            select(OrderORM).where(OrderORM.uuid_user == user_uuid)
        )
        order = result.scalar_one()
        assert order.total_price == Decimal("190.00")

    @pytest.mark.asyncio
    async def test_publishes_to_rabbitmq(
        self, client: AsyncClient, db_session: AsyncSession, mock_catalog_publish: MagicMock
    ):
        headers, user_uuid = _user_headers()
        await _seed_product_and_cart(db_session, user_uuid)

        response = await client.post("/order/create", headers=headers)
        assert response.status_code == 200

        mock_catalog_publish.publish.assert_awaited_once()
        call_args = mock_catalog_publish.publish.call_args
        assert call_args.args[0] == "catalog_order.deduct_from_stock"
        payload = call_args.args[1]
        assert "id_order" in payload
        assert payload["uuid_user"] == str(user_uuid)
        assert len(payload["products"]) == 1


class TestUpdateStatusOrder:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        _, user_uuid = _user_headers()
        order = await _seed_order(db_session, user_uuid)
        admin_headers = _admin_headers()

        response = await client.patch(
            "/order/update_status_order",
            json={"id_order": order.id, "status": "processing"},
            headers=admin_headers,
        )
        assert response.status_code == 200

        await db_session.refresh(order)
        assert order.status_order == OrderStatusEnum.PROCESSING

    @pytest.mark.asyncio
    async def test_order_not_found(self, client: AsyncClient):
        admin_headers = _admin_headers()
        response = await client.patch(
            "/order/update_status_order",
            json={"id_order": 99999, "status": "shipped"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_no_admin_token(self, client: AsyncClient):
        user_token = create_access_token({"uuid": str(uuid4())})
        response = await client.patch(
            "/order/update_status_order",
            json={"id_order": 1, "status": "shipped"},
            headers={"Cookie": f"admin_access_token={user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.patch(
            "/order/update_status_order",
            json={"id_order": 1, "status": "shipped"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_fields(self, client: AsyncClient):
        admin_headers = _admin_headers()
        response = await client.patch(
            "/order/update_status_order",
            json={},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestUpdateStatusPayment:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        _, user_uuid = _user_headers()
        order = await _seed_order(db_session, user_uuid)
        admin_headers = _admin_headers()

        response = await client.patch(
            "/order/update_status_payment",
            json={"id_order": order.id, "payment_success": True},
            headers=admin_headers,
        )
        assert response.status_code == 200

        await db_session.refresh(order)
        assert order.status_payment is True

    @pytest.mark.asyncio
    async def test_no_admin_token(self, client: AsyncClient):
        user_token = create_access_token({"uuid": str(uuid4())})
        response = await client.patch(
            "/order/update_status_payment",
            json={"id_order": 1, "payment_success": True},
            headers={"Cookie": f"admin_access_token={user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.patch(
            "/order/update_status_payment",
            json={"id_order": 1, "payment_success": True},
        )
        assert response.status_code == 401


class TestPayForOrder:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        headers, user_uuid = _user_headers()
        order = await _seed_order(db_session, user_uuid, total="250.00")

        response = await client.post(f"/order/pay_order/{order.id}", headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_order_not_found(self, client: AsyncClient):
        headers, _ = _user_headers()
        response = await client.post("/order/pay_order/99999", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_pay_others_order(self, client: AsyncClient, db_session: AsyncSession):
        _, owner_uuid = _user_headers()
        order = await _seed_order(db_session, owner_uuid)

        other_headers, _ = _user_headers()
        response = await client.post(f"/order/pay_order/{order.id}", headers=other_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.post("/order/pay_order/1")
        assert response.status_code == 401


class TestGetAllOrders:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        admin_headers = _admin_headers()
        response = await client.get("/order/list", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_orders(self, client: AsyncClient, db_session: AsyncSession):
        _, user_uuid = _user_headers()
        await _seed_order(db_session, user_uuid, total="100.00")
        await _seed_order(db_session, user_uuid, total="200.00")

        admin_headers = _admin_headers()
        response = await client.get("/order/list", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession):
        _, user_uuid = _user_headers()
        for i in range(5):
            await _seed_order(db_session, user_uuid, total=f"{i * 10}.00")

        admin_headers = _admin_headers()
        response = await client.get("/order/list?limit=2&offset=0", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response = await client.get("/order/list?limit=2&offset=4", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_no_admin_token(self, client: AsyncClient):
        user_token = create_access_token({"uuid": str(uuid4())})
        response = await client.get(
            "/order/list",
            headers={"Cookie": f"admin_access_token={user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/order/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_response_schema(self, client: AsyncClient, db_session: AsyncSession):
        _, user_uuid = _user_headers()
        await _seed_order(db_session, user_uuid, total="50.00")

        admin_headers = _admin_headers()
        response = await client.get("/order/list", headers=admin_headers)
        data = response.json()
        assert len(data) == 1
        order = data[0]
        assert "id" in order
        assert "uuid_user" in order
        assert "status_order" in order
        assert "status_payment" in order
        assert "created_at" in order
        assert "total_price" in order
        assert "items" in order
