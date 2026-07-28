from uuid import uuid4

import pytest
from pydantic import ValidationError

from srv_notification.src.modules.notification.routers import (
    PaginationSchema,
    UpdateNotifSchema,
)
from srv_notification.src.rabbit.schemas import RabbitAddNotificationSchema


class TestPaginationSchema:
    def test_defaults(self):
        schema = PaginationSchema()
        assert schema.limit == 20
        assert schema.offset == 0

    def test_custom_values(self):
        schema = PaginationSchema(limit=50, offset=10)
        assert schema.limit == 50
        assert schema.offset == 10

    def test_min_limit(self):
        schema = PaginationSchema(limit=1)
        assert schema.limit == 1

    def test_max_limit(self):
        schema = PaginationSchema(limit=100)
        assert schema.limit == 100

    def test_limit_zero_invalid(self):
        with pytest.raises(ValidationError):
            PaginationSchema(limit=0)

    def test_limit_exceeds_max(self):
        with pytest.raises(ValidationError):
            PaginationSchema(limit=101)

    def test_negative_offset(self):
        with pytest.raises(ValidationError):
            PaginationSchema(offset=-1)


class TestUpdateNotifSchema:
    def test_empty_list(self):
        schema = UpdateNotifSchema(uuid_notifications=[])
        assert schema.uuid_notifications == []

    def test_valid_uuids(self):
        uid1, uid2 = uuid4(), uuid4()
        schema = UpdateNotifSchema(uuid_notifications=[uid1, uid2])
        assert len(schema.uuid_notifications) == 2

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            UpdateNotifSchema()

    def test_invalid_uuid_type(self):
        with pytest.raises(ValidationError):
            UpdateNotifSchema(uuid_notifications=["not-a-uuid"])


class TestRabbitAddNotificationSchema:
    def test_valid(self):
        schema = RabbitAddNotificationSchema(
            uuid_user=uuid4(),
            title_notification="Order confirmed",
            message_notification="Your order is confirmed",
        )
        assert schema.title_notification == "Order confirmed"

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            RabbitAddNotificationSchema(
                uuid_user=uuid4(),
                title_notification="Title",
            )

    def test_invalid_uuid(self):
        with pytest.raises(ValidationError):
            RabbitAddNotificationSchema(
                uuid_user="not-a-uuid",
                title_notification="Title",
                message_notification="Message",
            )
