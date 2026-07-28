from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.security import create_access_token
from srv_auth.src.db.models.user import UserORM

VALID_REGISTER_PAYLOAD = {
    "number": "+79991234567",
    "password1": "secret123",
    "password2": "secret123",
    "email": "test@example.com",
    "country": "Russia",
    "city": "Moscow",
    "address": "Street 1",
}


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRegister:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        response = await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        assert response.status_code == 201
        token = response.json()
        assert isinstance(token, str)
        assert len(token) > 0

        result = await db_session.execute(select(UserORM).where(UserORM.number == "+79991234567"))
        user = result.scalar_one()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.country == "Russia"
        assert user.city == "Moscow"
        assert user.address == "Street 1"

    @pytest.mark.asyncio
    async def test_sets_cookie(self, client: AsyncClient):
        response = await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        set_cookie = response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie

    @pytest.mark.asyncio
    async def test_invalid_phone_no_plus(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "number": "79991234567",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_phone_too_short(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "number": "+7999",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_passwords_do_not_match(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "password2": "different123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_too_short(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "password1": "short",
                "password2": "short",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_with_spaces(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "password1": "with spaces",
                "password2": "with spaces",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_phone_raises_409(self, client: AsyncClient, db_session: AsyncSession):
        response1 = await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        assert response1.status_code == 201

        response2 = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "email": "other@example.com",
            },
        )
        assert response2.status_code == 409
        assert response2.json()["error_type"] == "UserPhoneAlreadyExists"

    @pytest.mark.asyncio
    async def test_duplicate_email_raises_409(self, client: AsyncClient, db_session: AsyncSession):
        response1 = await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        assert response1.status_code == 201

        response2 = await client.post(
            "/auth/register",
            json={
                **VALID_REGISTER_PAYLOAD,
                "number": "+79991234568",
            },
        )
        assert response2.status_code == 409
        assert response2.json()["error_type"] == "UserEmailAlreadyExists"

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        response = await client.post("/auth/register", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_publishes_to_rabbitmq(self, client: AsyncClient, db_session: AsyncSession, mock_rabbit_publish):
        response = await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)
        assert response.status_code == 201

        mock_rabbit_publish.publish.assert_awaited_once()
        call_args = mock_rabbit_publish.publish.call_args
        assert call_args.args[0] == "payment_auth.created"
        event_data = call_args.args[1]
        assert "uuid_user" in event_data
        assert event_data["number"] == "+79991234567"


class TestLogin:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession):
        await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        response = await client.post(
            "/auth/login",
            json={
                "number": "+79991234567",
                "password": "secret123",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sets_cookie(self, client: AsyncClient, db_session: AsyncSession):
        await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        response = await client.post(
            "/auth/login",
            json={
                "number": "+79991234567",
                "password": "secret123",
            },
        )

        set_cookie = response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie

    @pytest.mark.asyncio
    async def test_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        await client.post("/auth/register", json=VALID_REGISTER_PAYLOAD)

        response = await client.post(
            "/auth/login",
            json={
                "number": "+79991234567",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["error_type"] == "InvalidPassword"

    @pytest.mark.asyncio
    async def test_user_not_found(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "number": "+79999999999",
                "password": "secret123",
            },
        )

        assert response.status_code == 404
        assert response.json()["error_type"] == "UserNotFound"

    @pytest.mark.asyncio
    async def test_invalid_phone_format(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "number": "123",
                "password": "secret123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_fields(self, client: AsyncClient):
        response = await client.post("/auth/login", json={})
        assert response.status_code == 422


class TestLoginAdmin:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient):
        response = await client.post(
            "/auth/login_admin",
            json={
                "login": "admin",
                "password": "qwerty",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sets_cookie(self, client: AsyncClient):
        response = await client.post(
            "/auth/login_admin",
            json={
                "login": "admin",
                "password": "qwerty",
            },
        )

        set_cookie = response.headers.get("set-cookie", "")
        assert "admin_access_token=" in set_cookie

    @pytest.mark.asyncio
    async def test_wrong_login(self, client: AsyncClient):
        response = await client.post(
            "/auth/login_admin",
            json={
                "login": "wrong",
                "password": "qwerty",
            },
        )

        assert response.status_code == 404
        assert response.json()["error_type"] == "UserNotFound"

    @pytest.mark.asyncio
    async def test_wrong_password(self, client: AsyncClient):
        response = await client.post(
            "/auth/login_admin",
            json={
                "login": "admin",
                "password": "wrong",
            },
        )

        assert response.status_code == 401
        assert response.json()["error_type"] == "InvalidPassword"

    @pytest.mark.asyncio
    async def test_missing_fields(self, client: AsyncClient):
        response = await client.post("/auth/login_admin", json={})
        assert response.status_code == 422


class TestMe:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient):
        user_uuid = str(uuid4())
        token = create_access_token({"uuid": user_uuid})

        response = await client.get(
            "/auth/me",
            headers={"Cookie": f"access_token={token}"},
        )

        assert response.status_code == 200
        assert response.json() == user_uuid

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/auth/me",
            headers={"Cookie": "access_token=invalid_token_value"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"


class TestMeAdmin:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient):
        token = create_access_token({"uuid": "admin"})

        response = await client.get(
            "/auth/me_admin",
            headers={"Cookie": f"admin_access_token={token}"},
        )

        assert response.status_code == 200
        assert response.json() == "admin"

    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/auth/me_admin")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_non_admin_token(self, client: AsyncClient):
        token = create_access_token({"uuid": str(uuid4())})

        response = await client.get(
            "/auth/me_admin",
            headers={"Cookie": f"admin_access_token={token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Not admin"
