from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from srv_auth.src.db.session import get_db
from srv_auth.src.modules.auth.service import AuthService

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_auth_servise(db: DbDep) -> AuthService:
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_servise)]
