from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from srv_catalog.src.db.session import get_db


DbDep = Annotated[AsyncSession, Depends(get_db)]