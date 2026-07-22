from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from srv_payment.src.db.session import get_db


DbDep = Annotated[AsyncSession, Depends(get_db)]


"""
async def get_cart_product_cache_servise(db: DbDep) -> CartProductCacheService:
    return CartProductCacheService(db)

CartProductCacheServiceDep = Annotated[CartProductCacheService, Depends(get_cart_product_cache_servise)]
"""