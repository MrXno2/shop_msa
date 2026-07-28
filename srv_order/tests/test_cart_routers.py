from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.security import create_access_token
from srv_order.src.db.models.cart_user import CartORM
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM


def _user_headers(user_uuid=None):
    if user_uuid is None:
        user_uuid = uuid4()
    token = create_access_token({"uuid": str(user_uuid)})
    return {"Cookie": f"access_token={token}"}, user_uuid


def _admin_headers():
    token = create_access_token({"uuid": "admin"})
    return {"Cookie": f"admin_access_token={token}"}


async def _seed_cache_product(db: AsyncSession, uuid_product=None, name="Laptop", price="999.99", sale="100.00", image_url="http://img.jpg"):
    if uuid_product is None:
        uuid_product = uuid4()
    product = CartProductCacheORM(
        uuid_product=uuid_product,
        name=name,
        price=price,
        sale=sale,
        image_url=image_url,
    )
    db.add(product)
    await db.flush()
    return product


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAddProductInCart:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session)
        headers, user_uuid = _user_headers()

        response = await client.post(
            f"/cart/add/{product.uuid_product}",
            headers=headers,
        )
        assert response.status_code == 201

        result = await db_session.execute(
            select(CartORM).where(CartORM.uuid_user == user_uuid)
        )
        cart_item = result.scalar_one()
        assert cart_item is not None
        assert cart_item.uuid_product == product.uuid_product
        assert cart_item.count_product == 1

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.post(f"/cart/add/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_conflict_duplicate_product(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session)
        headers, user_uuid = _user_headers()

        response1 = await client.post(f"/cart/add/{product.uuid_product}", headers=headers)
        assert response1.status_code == 201

        response2 = await client.post(f"/cart/add/{product.uuid_product}", headers=headers)
        assert response2.status_code == 409

    @pytest.mark.asyncio
    async def test_different_users_can_add_same_product(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session)
        headers1, _ = _user_headers()
        headers2, _ = _user_headers()

        resp1 = await client.post(f"/cart/add/{product.uuid_product}", headers=headers1)
        resp2 = await client.post(f"/cart/add/{product.uuid_product}", headers=headers2)
        assert resp1.status_code == 201
        assert resp2.status_code == 201


class TestDeleteProductInCart:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session)
        headers, user_uuid = _user_headers()

        await client.post(f"/cart/add/{product.uuid_product}", headers=headers)

        response = await client.delete(f"/cart/del/{product.uuid_product}", headers=headers)
        assert response.status_code == 200

        result = await db_session.execute(
            select(CartORM).where(CartORM.uuid_user == user_uuid)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.delete(f"/cart/del/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_ok(self, client: AsyncClient):
        headers, _ = _user_headers()
        response = await client.delete(f"/cart/del/{uuid4()}", headers=headers)
        assert response.status_code == 200


class TestGetAllProductsInCart:
    @pytest.mark.asyncio
    async def test_empty_cart(self, client: AsyncClient):
        headers, _ = _user_headers()
        response = await client.get("/cart/get_all", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_products(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session, name="Phone", price="499.99", sale="50.00")
        headers, user_uuid = _user_headers()

        await client.post(f"/cart/add/{product.uuid_product}", headers=headers)

        response = await client.get("/cart/get_all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Phone"
        assert data[0]["price"] == "499.99"
        assert data[0]["sale"] == "50.00"
        assert data[0]["count_product"] == 1
        assert data[0]["uuid"] == str(product.uuid_product)

    @pytest.mark.asyncio
    async def test_only_own_cart(self, client: AsyncClient, db_session: AsyncSession):
        product = await _seed_cache_product(db_session)
        headers1, user1 = _user_headers()
        headers2, user2 = _user_headers()

        await client.post(f"/cart/add/{product.uuid_product}", headers=headers1)

        resp1 = await client.get("/cart/get_all", headers=headers1)
        resp2 = await client.get("/cart/get_all", headers=headers2)
        assert len(resp1.json()) == 1
        assert len(resp2.json()) == 0

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/cart/get_all")
        assert response.status_code == 401
