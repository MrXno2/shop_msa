from decimal import Decimal
from typing import Annotated
from uuid import UUID
from sqlalchemy import and_, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from core_app.security import is_admin_token, is_validity_token
from core_app.exception import ProductNotFound 
from srv_order.src.db.models.cart_product_cache import CartProductCacheORM
from srv_order.src.db.models.cart_user import CartORM
from srv_order.src.dependensies import DbDep
from sqlalchemy.exc import IntegrityError
from srv_order.src.schemas import CartCacheProductSchema


router = APIRouter(prefix="/cart")


class CartRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def add_product(self, data_cart: CartORM) -> None:
        self.db.add(data_cart)

    async def del_product(self, uuid_user: UUID, uuid_product: UUID) -> None:
        await self.db.execute(
            delete(CartORM)
            .where(
                CartORM.uuid_user == uuid_user,
                CartORM.uuid_product == uuid_product
            )
        )

    async def del_all_product(self, uuid_user: UUID) -> None:
        await self.db.execute(
            delete(CartORM)
            .where(
                CartORM.uuid_user == uuid_user
            )
        )

    async def get_all_product(self, uuid_user: UUID) -> list[tuple[CartProductCacheORM, CartORM]]:
        result = await self.db.execute(
            select(CartProductCacheORM, CartORM)
            .join(CartORM, CartORM.uuid_product == CartProductCacheORM.uuid_product)
            .where(CartORM.uuid_user == uuid_user)
        )
        
        return [tuple(row) for row in result.all()]
    
    async def get_product(self, uuid_user: UUID, uuid_product: UUID) -> CartORM | None:
        result = await self.db.execute(
            select(CartORM)
            .where(
                CartORM.uuid_user == uuid_user,
                CartORM.uuid_product == uuid_product
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
    

class CartService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.cart_repo = CartRepository(db)

    async def add_product(self, uuid_user: UUID, uuid_product: UUID) -> None:
        check_product = await self.cart_repo.get_product(uuid_user=uuid_user, uuid_product=uuid_product)
        if check_product is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Conflict product")

        product = CartORM(
            uuid_user = uuid_user,
            uuid_product = uuid_product
        )
        try:
            await self.cart_repo.add_product(product)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Product not found or already in cart")


    async def del_product(self, uuid_user: UUID, uuid_product: UUID) -> None:
        await self.cart_repo.del_product(uuid_user, uuid_product)
        await self.db.commit()


    async def get_all_product(self, uuid_user: UUID) -> list[CartCacheProductSchema]:
        products = await self.cart_repo.get_all_product(uuid_user)
        
        product_schemas = []
        for cache_product, cart in products:
            schema = CartCacheProductSchema(
                uuid=cache_product.uuid_product,
                name=cache_product.name,
                price=cache_product.price,
                sale=cache_product.sale,
                image_url=cache_product.image_url,
                count_product=cart.count_product
            )
            product_schemas.append(schema)
        
        return product_schemas


async def get_product_servise(db: DbDep) -> CartService:
    return CartService(db)


CartServiceDep = Annotated[CartService, Depends(get_product_servise)]
 

@router.post("/add/{uuid_product}", status_code=status.HTTP_201_CREATED)
async def add_product_in_cart(
    uuid_product: UUID, 
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await product_service.add_product(uuid_user=uuid_user, uuid_product=uuid_product)


@router.delete("/del/{uuid_product}", status_code=status.HTTP_200_OK)
async def delete_product_in_cart(
    uuid_product: UUID, 
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await product_service.del_product(uuid_user=uuid_user, uuid_product=uuid_product)


@router.get("/get_all", status_code=status.HTTP_200_OK)
async def get_list_products_cart(
    product_service: CartServiceDep,
    payload = Depends(is_validity_token)
) -> list[CartCacheProductSchema]:
    uuid_user = payload.get("uuid")
    return await product_service.get_all_product(uuid_user=uuid_user)
