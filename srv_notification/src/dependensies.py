from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from srv_notification.src.db.session import get_db

DbDep = Annotated[AsyncSession, Depends(get_db)]
