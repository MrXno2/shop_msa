import pytest
from pydantic import ValidationError
from uuid import uuid4

from srv_catalog.src.modules.product.schemas import ProductListQuerySchema


class TestProductListQuerySchema:
    def test_defaults(self):
        schema = ProductListQuerySchema()
        assert schema.category_id is None
        assert schema.min_price is None
        assert schema.max_price is None
        assert schema.in_stock is None
        assert schema.on_sale is None
        assert schema.search is None
        assert schema.sort_by == "name"
        assert schema.sort_order == "desc"
        assert schema.limit == 20
        assert schema.offset == 0

    def test_valid_category_id(self):
        uid = uuid4()
        schema = ProductListQuerySchema(category_id=uid)
        assert schema.category_id == uid

    def test_valid_price_range(self):
        schema = ProductListQuerySchema(min_price=10, max_price=100)
        assert schema.min_price == 10
        assert schema.max_price == 100

    def test_min_price_greater_than_max_price(self):
        schema = ProductListQuerySchema(min_price=100, max_price=10)
        assert schema.min_price > schema.max_price

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(min_price=-1)

    def test_invalid_sort_by(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(sort_by="invalid")

    def test_valid_sort_by_price(self):
        schema = ProductListQuerySchema(sort_by="price")
        assert schema.sort_by == "price"

    def test_valid_sort_by_stock(self):
        schema = ProductListQuerySchema(sort_by="stock")
        assert schema.sort_by == "stock"

    def test_invalid_sort_order(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(sort_order="up")

    def test_valid_sort_order_asc(self):
        schema = ProductListQuerySchema(sort_order="asc")
        assert schema.sort_order == "asc"

    def test_limit_too_small(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(limit=0)

    def test_limit_too_large(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(limit=101)

    def test_offset_negative(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(offset=-1)

    def test_search_too_long(self):
        with pytest.raises(ValidationError):
            ProductListQuerySchema(search="x" * 101)

    def test_in_stock_bool(self):
        schema = ProductListQuerySchema(in_stock=True)
        assert schema.in_stock is True

    def test_on_sale_bool(self):
        schema = ProductListQuerySchema(on_sale=True)
        assert schema.on_sale is True
