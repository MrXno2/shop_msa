from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from srv_order.src.modules.order.schemas import (
    OrderStatusUpdateSchema,
    PaginationSchema,
    PaymentStatusUpdateSchema,
)
from srv_order.src.rabbit.schemas import (
    CartCacheDeleteSchema,
    CartCacheProductSchema,
    ProductCacheSchema,
    RabbitAddNotificationSchema,
    RabbitOrderToCatalogSchema,
    RabbitPaymentStatusUpdateSchema,
    RabbitSendOrderPaymentSchema,
    RabbitStockResultSchema,
)


class TestPaginationSchema:
    def test_defaults(self):
        s = PaginationSchema()
        assert s.limit == 20
        assert s.offset == 0

    def test_custom(self):
        s = PaginationSchema(limit=50, offset=10)
        assert s.limit == 50
        assert s.offset == 10

    def test_limit_zero_invalid(self):
        with pytest.raises(ValidationError):
            PaginationSchema(limit=0)

    def test_limit_exceeds_max(self):
        with pytest.raises(ValidationError):
            PaginationSchema(limit=101)

    def test_negative_offset(self):
        with pytest.raises(ValidationError):
            PaginationSchema(offset=-1)


class TestOrderStatusUpdateSchema:
    def test_valid(self):
        s = OrderStatusUpdateSchema(id_order=1, status="processing")
        assert s.id_order == 1
        assert s.status == "processing"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            OrderStatusUpdateSchema()


class TestPaymentStatusUpdateSchema:
    def test_valid(self):
        s = PaymentStatusUpdateSchema(id_order=1, payment_success=True)
        assert s.payment_success is True

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            PaymentStatusUpdateSchema()


class TestCartCacheProductSchema:
    def test_valid(self):
        s = CartCacheProductSchema(
            uuid=uuid4(), name="Laptop", price="999.99", count_product=1
        )
        assert s.sale is None
        assert s.image_url is None

    def test_with_optional_fields(self):
        s = CartCacheProductSchema(
            uuid=uuid4(), name="Laptop", price="999.99",
            sale="100.00", image_url="http://img.jpg", count_product=2
        )
        assert s.sale == Decimal("100.00")


class TestRabbitSendOrderPaymentSchema:
    def test_valid(self):
        s = RabbitSendOrderPaymentSchema(
            uuid_user=uuid4(), id_order=1, total_price="100.00"
        )
        assert s.id_order == 1


class TestRabbitOrderToCatalogSchema:
    def test_valid(self):
        s = RabbitOrderToCatalogSchema(
            id_order=1, uuid_user=uuid4(), products=[{"name": "P"}]
        )
        assert len(s.products) == 1


class TestRabbitPaymentStatusUpdateSchema:
    def test_valid(self):
        s = RabbitPaymentStatusUpdateSchema(
            uuid_user=uuid4(), id_order=1, payment_success=True
        )
        assert s.error_message is None

    def test_with_error(self):
        s = RabbitPaymentStatusUpdateSchema(
            uuid_user=uuid4(), id_order=1, payment_success=False,
            error_message="Insufficient funds"
        )
        assert s.error_message == "Insufficient funds"


class TestProductCacheSchema:
    def test_valid(self):
        s = ProductCacheSchema(
            uuid=uuid4(), name="Phone", price="499.99"
        )
        assert s.sale is None


class TestRabbitStockResultSchema:
    def test_valid(self):
        s = RabbitStockResultSchema(
            id_order=1, uuid_user=uuid4(), status_order_type="created"
        )
        assert s.status_order_type == "created"


class TestCartCacheDeleteSchema:
    def test_valid(self):
        s = CartCacheDeleteSchema(uuid_product=uuid4())
        assert s.uuid_product is not None


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
