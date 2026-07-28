from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from core_app.security import create_access_token
from srv_catalog.src.db.models.category import CategoryORM
from srv_catalog.src.db.models.product import ProductORM


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCategoryAdd:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        response = await client.post(
            "/category/add",
            json={"name": "Electronics", "description": "Electronic devices"},
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()
        assert category is not None
        assert category.description == "Electronic devices"

    @pytest.mark.asyncio
    async def test_without_admin_token(self, client: AsyncClient):
        response = await client.post(
            "/category/add",
            json={"name": "Electronics"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_token(self, client: AsyncClient):
        token = create_access_token({"uuid": str(uuid4())})
        response = await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers={"Cookie": f"admin_access_token={token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_name(self, client: AsyncClient, admin_headers):
        response = await client.post(
            "/category/add",
            json={},
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_description_optional(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        response = await client.post(
            "/category/add",
            json={"name": "NoDesc"},
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "NoDesc"))
        category = result.scalar_one()
        assert category.description is None


class TestCategoryDelete:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "To Delete"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "To Delete"))
        category = result.scalar_one()

        response = await client.delete(
            f"/category/del/{category.uuid}",
            headers=admin_headers,
        )
        assert response.status_code == 200

        result = await db_session.execute(select(CategoryORM).where(CategoryORM.uuid == category.uuid))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_with_products_returns_409(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "With Products"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "With Products"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Test Product",
                "price": "10.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.delete(
            f"/category/del/{category.uuid}",
            headers=admin_headers,
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Category has products"

    @pytest.mark.asyncio
    async def test_without_admin_token(self, client: AsyncClient, db_session: AsyncSession):
        response = await client.delete(f"/category/del/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_category(self, client: AsyncClient, admin_headers):
        response = await client.delete(
            f"/category/del/{uuid4()}",
            headers=admin_headers,
        )
        assert response.status_code == 200


class TestCategoryList:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/category/all")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_categories(self, client: AsyncClient, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Cat1", "description": "Desc1"},
            headers=admin_headers,
        )
        await client.post(
            "/category/add",
            json={"name": "Cat2", "description": "Desc2"},
            headers=admin_headers,
        )

        response = await client.get("/category/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {c["name"] for c in data}
        assert names == {"Cat1", "Cat2"}

    @pytest.mark.asyncio
    async def test_response_schema(self, client: AsyncClient, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Schema Test", "description": "Test desc"},
            headers=admin_headers,
        )

        response = await client.get("/category/all")
        data = response.json()
        assert len(data) == 1
        item = data[0]
        assert "uuid" in item
        assert item["name"] == "Schema Test"
        assert item["description"] == "Test desc"


class TestProductCreate:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        response = await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "description": "Gaming laptop",
                "price": "999.99",
                "sale": "899.99",
                "stock": 10,
                "image_url": "http://example.com/laptop.jpg",
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        assert response.status_code == 201

        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()
        assert product is not None
        assert product.price == Decimal("999.99")
        assert product.sale == Decimal("899.99")
        assert product.stock == 10
        assert product.category_id == category.uuid

    @pytest.mark.asyncio
    async def test_without_admin_token(self, client: AsyncClient):
        response = await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_token(self, client: AsyncClient):
        token = create_access_token({"uuid": str(uuid4())})
        response = await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(uuid4()),
            },
            headers={"Cookie": f"admin_access_token={token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient, admin_headers):
        response = await client.post(
            "/product/create",
            json={},
            headers=admin_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_optional_fields_default(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Cat"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        response = await client.post(
            "/product/create",
            json={
                "name": "Minimal",
                "price": "5.00",
                "stock": 1,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        assert response.status_code == 201

        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Minimal"))
        product = result.scalar_one()
        assert product.description is None
        assert product.sale is None
        assert product.image_url is None

    @pytest.mark.asyncio
    async def test_publishes_to_rabbitmq(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_headers,
        mock_rabbit_publish,
    ):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        response = await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        assert response.status_code == 201

        mock_rabbit_publish.publish.assert_awaited_once()
        call_args = mock_rabbit_publish.publish.call_args
        assert call_args.args[0] == "catalog_order.created"


class TestProductGet:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "description": "Gaming",
                "price": "999.99",
                "sale": "899.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()

        response = await client.get(f"/product/get/{product.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Laptop"
        assert data["description"] == "Gaming"
        assert data["price"] == "999.99"
        assert data["sale"] == "899.99"
        assert data["stock"] == 10
        assert data["category_id"] == str(category.uuid)

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient):
        response = await client.get(f"/product/get/{uuid4()}")
        assert response.status_code == 404
        assert response.json()["error_type"] == "ProductNotFound"


class TestProductGetList:
    @pytest.mark.asyncio
    async def test_empty_list(self, client: AsyncClient):
        response = await client.get("/product/get_list")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_returns_products(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Phone",
                "price": "499.99",
                "stock": 20,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_filter_by_category(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat1"}, headers=admin_headers)
        await client.post("/category/add", json={"name": "Cat2"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM))
        categories = {c.name: c.uuid for c in result.scalars().all()}

        await client.post(
            "/product/create",
            json={
                "name": "Prod1",
                "price": "10.00",
                "stock": 5,
                "category_id": str(categories["Cat1"]),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Prod2",
                "price": "20.00",
                "stock": 5,
                "category_id": str(categories["Cat2"]),
            },
            headers=admin_headers,
        )

        response = await client.get(f"/product/get_list?category_id={categories['Cat1']}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Prod1"

    @pytest.mark.asyncio
    async def test_filter_by_price_range(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Cheap",
                "price": "5.00",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Expensive",
                "price": "50.00",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?min_price=10&max_price=100")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Expensive"

    @pytest.mark.asyncio
    async def test_filter_by_in_stock(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "InStock",
                "price": "10.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "OutOfStock",
                "price": "10.00",
                "stock": 0,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?in_stock=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "InStock"

    @pytest.mark.asyncio
    async def test_filter_by_on_sale(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "OnSale",
                "price": "10.00",
                "sale": "8.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "NoSale",
                "price": "10.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?on_sale=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "OnSale"

    @pytest.mark.asyncio
    async def test_filter_by_search(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Gaming Laptop",
                "description": "High performance",
                "price": "999.99",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Office Chair",
                "description": "Comfortable",
                "price": "99.99",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?search=Gaming")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Gaming Laptop"

    @pytest.mark.asyncio
    async def test_search_in_description(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "description": "Gaming performance",
                "price": "999.99",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?search=performance")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_sort_by_price_asc(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Expensive",
                "price": "50.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Cheap",
                "price": "5.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?sort_by=price&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["name"] == "Cheap"
        assert data["items"][1]["name"] == "Expensive"

    @pytest.mark.asyncio
    async def test_sort_by_name_desc(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Apple",
                "price": "5.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Banana",
                "price": "5.00",
                "stock": 5,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?sort_by=name&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["name"] == "Banana"
        assert data["items"][1]["name"] == "Apple"

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        for i in range(5):
            await client.post(
                "/product/create",
                json={
                    "name": f"Product{i}",
                    "price": f"{i}.00",
                    "stock": 5,
                    "category_id": str(category.uuid),
                },
                headers=admin_headers,
            )

        response = await client.get("/product/get_list?limit=2&offset=0&sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0

        response = await client.get("/product/get_list?limit=2&offset=4&sort_by=name&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_combined_filters(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post("/category/add", json={"name": "Cat"}, headers=admin_headers)
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Cat"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "sale": "899.99",
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        await client.post(
            "/product/create",
            json={
                "name": "Phone",
                "price": "499.99",
                "stock": 0,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )

        response = await client.get("/product/get_list?in_stock=true&on_sale=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Laptop"


class TestProductFullUpdate:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()

        response = await client.patch(
            "/product/full_update",
            json={
                "uuid": str(product.uuid),
                "name": "Gaming Laptop",
                "description": "Updated description",
                "price": "1299.99",
                "sale": "1199.99",
                "stock": 15,
                "image_url": "http://example.com/updated.jpg",
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        await db_session.refresh(product)
        assert product.name == "Gaming Laptop"
        assert product.description == "Updated description"
        assert product.price == Decimal("1299.99")
        assert product.sale == Decimal("1199.99")
        assert product.stock == 15
        assert product.image_url == "http://example.com/updated.jpg"

    @pytest.mark.asyncio
    async def test_not_found(self, client: AsyncClient, admin_headers):
        response = await client.patch(
            "/product/full_update",
            json={
                "uuid": str(uuid4()),
                "name": "Does Not Exist",
                "price": "10.00",
                "stock": 1,
                "category_id": str(uuid4()),
            },
            headers=admin_headers,
        )
        assert response.status_code == 404
        assert response.json()["error_type"] == "ProductNotFound"

    @pytest.mark.asyncio
    async def test_without_admin_token(self, client: AsyncClient):
        response = await client.patch(
            "/product/full_update",
            json={
                "uuid": str(uuid4()),
                "name": "Test",
                "price": "10.00",
                "stock": 1,
                "category_id": str(uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_publishes_to_rabbitmq(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_headers,
        mock_rabbit_publish,
    ):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()

        mock_rabbit_publish.publish.reset_mock()

        response = await client.patch(
            "/product/full_update",
            json={
                "uuid": str(product.uuid),
                "name": "Updated Laptop",
                "price": "1099.99",
                "stock": 12,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

        mock_rabbit_publish.publish.assert_awaited_once()
        call_args = mock_rabbit_publish.publish.call_args
        assert call_args.args[0] == "catalog_order.update"


class TestProductDelete:
    @pytest.mark.asyncio
    async def test_success(self, client: AsyncClient, db_session: AsyncSession, admin_headers):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()

        response = await client.delete(
            f"/product/delete/{product.uuid}",
            headers=admin_headers,
        )
        assert response.status_code == 204

        result = await db_session.execute(select(ProductORM).where(ProductORM.uuid == product.uuid))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_nonexistent_product(self, client: AsyncClient, admin_headers):
        response = await client.delete(
            f"/product/delete/{uuid4()}",
            headers=admin_headers,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_without_admin_token(self, client: AsyncClient):
        response = await client.delete(f"/product/delete/{uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_publishes_to_rabbitmq(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_headers,
        mock_rabbit_publish,
    ):
        await client.post(
            "/category/add",
            json={"name": "Electronics"},
            headers=admin_headers,
        )
        result = await db_session.execute(select(CategoryORM).where(CategoryORM.name == "Electronics"))
        category = result.scalar_one()

        await client.post(
            "/product/create",
            json={
                "name": "Laptop",
                "price": "999.99",
                "stock": 10,
                "category_id": str(category.uuid),
            },
            headers=admin_headers,
        )
        result = await db_session.execute(select(ProductORM).where(ProductORM.name == "Laptop"))
        product = result.scalar_one()

        mock_rabbit_publish.publish.reset_mock()

        response = await client.delete(
            f"/product/delete/{product.uuid}",
            headers=admin_headers,
        )
        assert response.status_code == 204

        mock_rabbit_publish.publish.assert_awaited_once()
        call_args = mock_rabbit_publish.publish.call_args
        assert call_args.args[0] == "catalog_order.delete"
