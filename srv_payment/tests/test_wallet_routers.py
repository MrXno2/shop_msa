from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.security import create_access_token
from srv_payment.src.db.models.history_wallet import HistoryWalletORM
from srv_payment.src.db.models.wallet import WalletORM


def _user_headers(user_uuid=None):
    if user_uuid is None:
        user_uuid = uuid4()
    token = create_access_token({"uuid": str(user_uuid)})
    return {"Cookie": f"access_token={token}"}, user_uuid


def _admin_headers():
    token = create_access_token({"uuid": "admin"})
    return {"Cookie": f"admin_access_token={token}"}


async def _seed_wallet(db: AsyncSession, user_uuid=None, balance="0.00", number=None):
    if user_uuid is None:
        user_uuid = uuid4()
    if number is None:
        number = f"+79{uuid4().hex[:8]}"
    wallet = WalletORM(uuid_user=user_uuid, number=number, balance=balance)
    db.add(wallet)
    await db.flush()
    return wallet


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestDepositBalance:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="0.00")
        admin_headers = _admin_headers()

        response = await client.post(
            "/payment/deposit",
            json={"uuid_user": str(user_uuid), "dep_price": "500.00"},
            headers=admin_headers,
        )
        assert response.status_code == 200

        await db_session.refresh(
            (await db_session.execute(
                select(WalletORM).where(WalletORM.uuid_user == user_uuid)
            )).scalar_one()
        )
        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet.balance == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_creates_history_record(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid)
        admin_headers = _admin_headers()

        await client.post(
            "/payment/deposit",
            json={"uuid_user": str(user_uuid), "dep_price": "100.00"},
            headers=admin_headers,
        )

        result = await db_session.execute(
            select(HistoryWalletORM).where(HistoryWalletORM.uuid_user == user_uuid)
        )
        history = result.scalar_one()
        assert history.transaction_type == "deposited"
        assert history.amount == Decimal("100.00")
        assert history.order_id is None
        assert history.comment is None

    @pytest.mark.asyncio
    async def test_cumulative_deposit(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="100.00")
        admin_headers = _admin_headers()

        await client.post(
            "/payment/deposit",
            json={"uuid_user": str(user_uuid), "dep_price": "250.00"},
            headers=admin_headers,
        )

        result = await db_session.execute(
            select(WalletORM).where(WalletORM.uuid_user == user_uuid)
        )
        wallet = result.scalar_one()
        assert wallet.balance == Decimal("350.00")

    @pytest.mark.asyncio
    async def test_user_not_found(self, client: AsyncClient):
        admin_headers = _admin_headers()
        response = await client.post(
            "/payment/deposit",
            json={"uuid_user": str(uuid4()), "dep_price": "100.00"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_no_admin_token(self, client: AsyncClient):
        user_token = create_access_token({"uuid": str(uuid4())})
        response = await client.post(
            "/payment/deposit",
            json={"uuid_user": str(uuid4()), "dep_price": "100.00"},
            headers={"Cookie": f"admin_access_token={user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.post(
            "/payment/deposit",
            json={"uuid_user": str(uuid4()), "dep_price": "100.00"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_fields(self, client: AsyncClient):
        admin_headers = _admin_headers()
        response = await client.post(
            "/payment/deposit",
            json={},
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestGetBalance:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="1234.56")
        headers, _ = _user_headers(user_uuid)

        response = await client.get("/payment/balance", headers=headers)
        assert response.status_code == 200
        assert response.json() == "1234.56"

    @pytest.mark.asyncio
    async def test_zero_balance(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        await _seed_wallet(db_session, user_uuid, balance="0.00")
        headers, _ = _user_headers(user_uuid)

        response = await client.get("/payment/balance", headers=headers)
        assert response.status_code == 200
        assert response.json() == "0.00"

    @pytest.mark.asyncio
    async def test_wallet_not_found(self, client: AsyncClient):
        headers, _ = _user_headers()
        response = await client.get("/payment/balance", headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_only_own_balance(self, client: AsyncClient, db_session: AsyncSession):
        user_a = uuid4()
        user_b = uuid4()
        await _seed_wallet(db_session, user_a, balance="100.00")
        await _seed_wallet(db_session, user_b, balance="999.00")

        headers_a, _ = _user_headers(user_a)
        headers_b, _ = _user_headers(user_b)

        resp_a = await client.get("/payment/balance", headers=headers_a)
        resp_b = await client.get("/payment/balance", headers=headers_b)
        assert resp_a.json() == "100.00"
        assert resp_b.json() == "999.00"

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/payment/balance")
        assert response.status_code == 401
