from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.security import create_access_token
from srv_notification.src.db.models.notification import NotificationORM


def _auth_headers(user_uuid=None) -> dict:
    if user_uuid is None:
        user_uuid = uuid4()
    token = create_access_token({"uuid": str(user_uuid)})
    return {"Cookie": f"access_token={token}"}


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestGetUnreadCount:
    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/notification/count")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/notification/count",
            headers={"Cookie": "access_token=invalid_token_value"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_zero_unread(self, client: AsyncClient):
        user_uuid = uuid4()
        response = await client.get(
            "/notification/count",
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200
        assert response.json() == 0

    @pytest.mark.asyncio
    async def test_counts_only_unread(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()

        for i in range(3):
            db_session.add(
                NotificationORM(
                    uuid_user=user_uuid,
                    title_notification=f"Title {i}",
                    message_notification=f"Message {i}",
                    is_read=False,
                )
            )
        db_session.add(
            NotificationORM(
                uuid_user=user_uuid,
                title_notification="Read",
                message_notification="Already read",
                is_read=True,
            )
        )
        await db_session.flush()

        response = await client.get(
            "/notification/count",
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200
        assert response.json() == 3

    @pytest.mark.asyncio
    async def test_only_own_notifications(self, client: AsyncClient, db_session: AsyncSession):
        user_a = uuid4()
        user_b = uuid4()

        db_session.add(
            NotificationORM(
                uuid_user=user_a,
                title_notification="A",
                message_notification="msg",
                is_read=False,
            )
        )
        db_session.add(
            NotificationORM(
                uuid_user=user_b,
                title_notification="B",
                message_notification="msg",
                is_read=False,
            )
        )
        await db_session.flush()

        response = await client.get(
            "/notification/count",
            headers=_auth_headers(user_a),
        )
        assert response.status_code == 200
        assert response.json() == 1


class TestGetNotifications:
    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.get("/notification/all")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get(
            "/notification/all",
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_notifications(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notif = NotificationORM(
            uuid_user=user_uuid,
            title_notification="Order created",
            message_notification="Your order #123 has been created",
            is_read=False,
        )
        db_session.add(notif)
        await db_session.flush()

        response = await client.get(
            "/notification/all",
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title_notification"] == "Order created"
        assert data[0]["message_notification"] == "Your order #123 has been created"
        assert data[0]["is_read"] is False
        assert data[0]["uuid_user"] == str(user_uuid)
        assert "uuid" in data[0]
        assert "created_at" in data[0]

    @pytest.mark.asyncio
    async def test_pagination_limit(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        for i in range(5):
            db_session.add(
                NotificationORM(
                    uuid_user=user_uuid,
                    title_notification=f"Title {i}",
                    message_notification=f"Message {i}",
                )
            )
        await db_session.flush()

        response = await client.get(
            "/notification/all?limit=2&offset=0",
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_pagination_offset(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        for i in range(5):
            db_session.add(
                NotificationORM(
                    uuid_user=user_uuid,
                    title_notification=f"Title {i}",
                    message_notification=f"Message {i}",
                )
            )
        await db_session.flush()

        response = await client.get(
            "/notification/all?limit=2&offset=4",
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title_notification"] == "Title 4"

    @pytest.mark.asyncio
    async def test_only_own_notifications(self, client: AsyncClient, db_session: AsyncSession):
        user_a = uuid4()
        user_b = uuid4()

        db_session.add(
            NotificationORM(
                uuid_user=user_a, title_notification="A", message_notification="a"
            )
        )
        db_session.add(
            NotificationORM(
                uuid_user=user_b, title_notification="B", message_notification="b"
            )
        )
        await db_session.flush()

        response = await client.get(
            "/notification/all",
            headers=_auth_headers(user_a),
        )
        data = response.json()
        assert len(data) == 1
        assert data[0]["title_notification"] == "A"

    @pytest.mark.asyncio
    async def test_invalid_limit_zero(self, client: AsyncClient):
        response = await client.get(
            "/notification/all?limit=0",
            headers=_auth_headers(),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_limit_exceeds_max(self, client: AsyncClient):
        response = await client.get(
            "/notification/all?limit=101",
            headers=_auth_headers(),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_offset_negative(self, client: AsyncClient):
        response = await client.get(
            "/notification/all?offset=-1",
            headers=_auth_headers(),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_response_schema_fields(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notif = NotificationORM(
            uuid_user=user_uuid,
            title_notification="Test",
            message_notification="Body",
            is_read=False,
        )
        db_session.add(notif)
        await db_session.flush()

        response = await client.get(
            "/notification/all",
            headers=_auth_headers(user_uuid),
        )
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert set(item.keys()) == {
            "uuid",
            "uuid_user",
            "title_notification",
            "message_notification",
            "created_at",
            "is_read",
        }


class TestUpdateReadNotification:
    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": []},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_mark_as_read(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notif = NotificationORM(
            uuid_user=user_uuid,
            title_notification="To mark",
            message_notification="Body",
            is_read=False,
        )
        db_session.add(notif)
        await db_session.flush()

        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": [str(notif.uuid)]},
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200

        await db_session.refresh(notif)
        assert notif.is_read is True

    @pytest.mark.asyncio
    async def test_empty_list_is_noop(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notif = NotificationORM(
            uuid_user=user_uuid,
            title_notification="Stay unread",
            message_notification="Body",
            is_read=False,
        )
        db_session.add(notif)
        await db_session.flush()

        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": []},
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200

        await db_session.refresh(notif)
        assert notif.is_read is False

    @pytest.mark.asyncio
    async def test_cannot_mark_others_notifications(self, client: AsyncClient, db_session: AsyncSession):
        user_a = uuid4()
        user_b = uuid4()

        notif_a = NotificationORM(
            uuid_user=user_a,
            title_notification="A's notif",
            message_notification="Body",
            is_read=False,
        )
        db_session.add(notif_a)
        await db_session.flush()

        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": [str(notif_a.uuid)]},
            headers=_auth_headers(user_b),
        )
        assert response.status_code == 200

        await db_session.refresh(notif_a)
        assert notif_a.is_read is False

    @pytest.mark.asyncio
    async def test_mark_multiple_as_read(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notifs = []
        for i in range(3):
            n = NotificationORM(
                uuid_user=user_uuid,
                title_notification=f"Notif {i}",
                message_notification=f"Body {i}",
                is_read=False,
            )
            db_session.add(n)
            notifs.append(n)
        await db_session.flush()

        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": [str(n.uuid) for n in notifs]},
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200

        for n in notifs:
            await db_session.refresh(n)
            assert n.is_read is True

    @pytest.mark.asyncio
    async def test_partial_update(self, client: AsyncClient, db_session: AsyncSession):
        user_uuid = uuid4()
        notif_read = NotificationORM(
            uuid_user=user_uuid,
            title_notification="Will be read",
            message_notification="Body",
            is_read=False,
        )
        notif_stay = NotificationORM(
            uuid_user=user_uuid,
            title_notification="Will stay unread",
            message_notification="Body",
            is_read=False,
        )
        db_session.add(notif_read)
        db_session.add(notif_stay)
        await db_session.flush()

        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": [str(notif_read.uuid)]},
            headers=_auth_headers(user_uuid),
        )
        assert response.status_code == 200

        await db_session.refresh(notif_read)
        await db_session.refresh(notif_stay)
        assert notif_read.is_read is True
        assert notif_stay.is_read is False

    @pytest.mark.asyncio
    async def test_missing_uuid_notifications_field(self, client: AsyncClient):
        response = await client.patch(
            "/notification/update",
            json={},
            headers=_auth_headers(),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_uuid_in_list(self, client: AsyncClient):
        response = await client.patch(
            "/notification/update",
            json={"uuid_notifications": ["not-a-uuid"]},
            headers=_auth_headers(),
        )
        assert response.status_code == 422
