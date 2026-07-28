from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from srv_notification.src.db.models.notification import NotificationORM
from srv_notification.src.rabbit.schemas import RabbitAddNotificationSchema
from srv_notification.src.rabbit.services import RabbitNotificationService


class TestRabbitNotificationService:
    @pytest.mark.asyncio
    async def test_add_notification_creates_record(self, db_session: AsyncSession):
        user_uuid = uuid4()
        payload = RabbitAddNotificationSchema(
            uuid_user=user_uuid,
            title_notification="Order created",
            message_notification="Your order #123 is confirmed",
        )

        message = MagicMock()
        message.body = payload.model_dump_json().encode()

        service = RabbitNotificationService()

        with pytest.MonkeyPatch.context() as m:
            import srv_notification.src.rabbit.services as svc

            original_db_session = svc.db_session

            class FakeSession:
                async def __aenter__(self):
                    return db_session

                async def __aexit__(self, *args):
                    pass

            m.setattr(svc, "db_session", FakeSession)

            await service.add_notification(message)

        result = await db_session.execute(
            select(NotificationORM).where(NotificationORM.uuid_user == user_uuid)
        )
        notif = result.scalar_one()
        assert notif is not None
        assert notif.title_notification == "Order created"
        assert notif.message_notification == "Your order #123 is confirmed"
        assert notif.is_read is False
        assert notif.created_at is not None

    @pytest.mark.asyncio
    async def test_add_notification_invalid_json(self, db_session: AsyncSession):
        message = MagicMock()
        message.body = b"not valid json"

        service = RabbitNotificationService()

        class FakeSession:
            async def __aenter__(self):
                return db_session

            async def __aexit__(self, *args):
                pass

        with pytest.MonkeyPatch.context() as m:
            import srv_notification.src.rabbit.services as svc

            m.setattr(svc, "db_session", FakeSession)

            with pytest.raises(Exception):
                await service.add_notification(message)

    @pytest.mark.asyncio
    async def test_add_notification_multiple(self, db_session: AsyncSession):
        service = RabbitNotificationService()

        class FakeSession:
            async def __aenter__(self):
                return db_session

            async def __aexit__(self, *args):
                pass

        for i in range(3):
            payload = RabbitAddNotificationSchema(
                uuid_user=uuid4(),
                title_notification=f"Title {i}",
                message_notification=f"Message {i}",
            )
            message = MagicMock()
            message.body = payload.model_dump_json().encode()

            with pytest.MonkeyPatch.context() as m:
                import srv_notification.src.rabbit.services as svc

                m.setattr(svc, "db_session", FakeSession)

                await service.add_notification(message)

        result = await db_session.execute(select(NotificationORM))
        notifs = result.scalars().all()
        assert len(notifs) == 3
