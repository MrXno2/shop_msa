from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from srv_payment.src.modules.wallet.schemas import DepositWalletSchema
from srv_payment.src.rabbit.schemas import (
    RabbitAddNotificationSchema,
    RabbitRequestOrderPaymentSchema,
    RabbitResponseOrderPaymentSchema,
    RabbitWalletUserSchema,
)


class TestDepositWalletSchema:
    def test_valid(self):
        s = DepositWalletSchema(uuid_user=uuid4(), dep_price="100.00")
        assert s.dep_price == Decimal("100.00")

    def test_zero_deposit(self):
        s = DepositWalletSchema(uuid_user=uuid4(), dep_price="0.00")
        assert s.dep_price == Decimal("0.00")

    def test_missing_uuid_user(self):
        with pytest.raises(ValidationError):
            DepositWalletSchema(dep_price="100.00")

    def test_missing_dep_price(self):
        with pytest.raises(ValidationError):
            DepositWalletSchema(uuid_user=uuid4())

    def test_invalid_uuid(self):
        with pytest.raises(ValidationError):
            DepositWalletSchema(uuid_user="not-a-uuid", dep_price="100.00")


class TestRabbitWalletUserSchema:
    def test_valid(self):
        s = RabbitWalletUserSchema(uuid_user=uuid4(), number="+79991234567")
        assert s.number == "+79991234567"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RabbitWalletUserSchema()


class TestRabbitRequestOrderPaymentSchema:
    def test_valid(self):
        s = RabbitRequestOrderPaymentSchema(
            uuid_user=uuid4(), id_order=1, total_price="250.00"
        )
        assert s.id_order == 1
        assert s.total_price == Decimal("250.00")

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RabbitRequestOrderPaymentSchema()


class TestRabbitResponseOrderPaymentSchema:
    def test_valid_success(self):
        s = RabbitResponseOrderPaymentSchema(
            uuid_user=uuid4(), id_order=1, payment_success=True
        )
        assert s.payment_success is True
        assert s.error_message is None

    def test_valid_failure(self):
        s = RabbitResponseOrderPaymentSchema(
            uuid_user=uuid4(), id_order=1, payment_success=False,
            error_message="Insufficient funds"
        )
        assert s.error_message == "Insufficient funds"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            RabbitResponseOrderPaymentSchema()


class TestRabbitAddNotificationSchema:
    def test_valid(self):
        s = RabbitAddNotificationSchema(
            uuid_user=uuid4(),
            title_notification="Title",
            message_notification="Message",
        )
        assert s.title_notification == "Title"

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            RabbitAddNotificationSchema(uuid_user=uuid4())
