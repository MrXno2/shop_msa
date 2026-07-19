from decimal import Decimal
from typing import Annotated
from uuid import UUID
from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from core_app.security import is_admin_token
from core_app.exception import ProductNotFound 
from srv_order.src.db.session import db_session
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.dependensies import DbDep
from sqlalchemy.exc import IntegrityError
import json
import aio_pika



class CartCacheProductSchema(BaseModel):
    model_config = {"from_attributes": True}

    uuid: UUID
    name: str
    price: Decimal
    sale: Decimal
    image_url: str


class CartCacheDeleteSchema(BaseModel):
    model_config = {"from_attributes": True}

    uuid_product: UUID


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    

    async def create_product(self, data_product: CartProductCacheORM) -> None:
        self.db.add(data_product)
    

    async def del_product(self, uuid_product: UUID) -> None:
        await self.db.execute(
            delete(CartProductCacheORM)
            .where(CartProductCacheORM.uuid_product == uuid_product)
        )


    async def full_update_product(self, req_data: dict) -> None:
        await self.db.execute(
            update(CartProductCacheORM)
            .where(CartProductCacheORM.uuid_product == req_data["uuid_product"])
            .values(**req_data)
        )


    async def get_product(self, uuid_product: UUID) -> CartProductCacheORM | None:
        product = await self.db.execute(
            select(CartProductCacheORM)
            .where(CartProductCacheORM.uuid_product == uuid_product)
            .limit(1)
        )
        return product.scalar_one_or_none()
    

class CartProductCacheService():
    async def create_product(
        self, 
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = ProductRepository(db)
            data = CartCacheProductSchema.model_validate_json(message.body)
            product = CartProductCacheORM(
                uuid_product = data.uuid,
                name = data.name,
                price = data.price,
                sale = data.sale,
                image_url = data.image_url
            )
            try:
                await product_repo.create_product(product)
                await db.commit()
            except IntegrityError:
                await db.rollback()
            
            print(data)


    async def del_product(
        self,
        message: aio_pika.IncomingMessage
    ) -> None:
        async with db_session() as db:
            product_repo = ProductRepository(db)
            data = CartCacheDeleteSchema.model_validate_json(message.body)

            await product_repo.del_product(data.uuid_product)
            await db.commit()

            print(data)


    async def full_update_product(
        self,
        message: aio_pika.IncomingMessage,
    ) -> None:
        async with db_session() as db:
            product_repo = ProductRepository(db)
            data = CartCacheProductSchema.model_validate_json(message.body)

            product = await product_repo.get_product(data.uuid)
            if not product:
                raise ProductNotFound()
            
            new_data = data.model_dump()
            new_data["uuid_product"] = new_data.pop("uuid")

            await product_repo.full_update_product(new_data)
            await db.commit()

            print(data)