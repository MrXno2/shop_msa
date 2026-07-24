from decimal import Decimal
from enum import Enum
from typing import List
from uuid import UUID
from core_app.rabbit import rabbit_catalog_order
import aio_pika
from pydantic import BaseModel
from srv_catalog.src.db.session import db_session
from srv_catalog.src.routers.product import ProductRepository


class OrderStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class RabbitRequestOrderProducts(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID
    name: str
    price: Decimal
    sale: Decimal
    image_url: str
    count_product: int


class RabbitRequestOrder(BaseModel):
    id_order: int
    uuid_user: UUID
    products: List[RabbitRequestOrderProducts]


class RabbitResponseCatalog(BaseModel):
    id_order: int
    uuid_user: UUID
    status_order_type: str


class RabbitCatalogOrderService:
    async def deduct_from_stock(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = ProductRepository(db)
            data = RabbitRequestOrder.model_validate_json(message.body)  
            resp_rabbit = RabbitResponseCatalog(
                id_order = data.id_order,
                uuid_user = data.uuid_user,
                status_order_type = OrderStatus.CREATED
            )   
            success = True
            for product in data.products:
                update_product_stock = await product_repo.deduct_from_stock(product)
                if update_product_stock is None:
                    await db.rollback()
                    # отправка в раббит что остаток не совпал
                    resp_rabbit.status_order_type = OrderStatus.CANCELLED
                    success = False
                    break
            if success:
                await db.commit()
            # отправка в раббит что заказ успешно сформирован
            await rabbit_catalog_order.publish(
                "catalog_order.handle_stock_deduction_result", 
                resp_rabbit.model_dump(mode="json")
            )