from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update
from core_app.security import is_validity_token
from sqlalchemy.ext.asyncio import AsyncSession
from srv_notification.src.db.models.notification import NotificationORM
from srv_notification.src.dependensies import DbDep


router = APIRouter(prefix="/notification")


class PaginationSchema(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ResponseAllNotifSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    uuid_user: UUID
    title_notification: str
    message_notification: str
    created_at: datetime
    is_read: bool


class UpdateNotifSchema(BaseModel):
    uuid_notifications: list[UUID]


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_notification(self, notif: NotificationORM) -> None:
        self.db.add(notif)

    async def get_unread_count(self, uuid_user: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(NotificationORM)
            .where(
                NotificationORM.uuid_user == uuid_user,
                NotificationORM.is_read == False
            )
        )
        return result.scalar_one()

    async def get_notifications(
        self,
        uuid_user: UUID,
        pagination: PaginationSchema
    ) -> list[NotificationORM]:
        result = await self.db.execute(
            select(NotificationORM)
            .where(NotificationORM.uuid_user == uuid_user)
            .limit(pagination.limit)
            .offset(pagination.offset)
        )
        return list(result.scalars().all())

    async def update_read_notification(
        self, 
        uuid_user: UUID,
        req_update_notif: UpdateNotifSchema
    ) -> None:
        if not req_update_notif.uuid_notifications:
            return
        query = (
            update(NotificationORM)
            .where(
                NotificationORM.uuid_user == uuid_user,
                NotificationORM.uuid.in_(req_update_notif.uuid_notifications)
            )
            .values(is_read = True)
        )
        await self.db.execute(query)



class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.notif_repo = NotificationRepository(db)

    async def update_read_notification(
        self, 
        uuid_user: UUID,
        req_update_notif: UpdateNotifSchema
    ) -> None:
        await self.notif_repo.update_read_notification(uuid_user=uuid_user, req_update_notif=req_update_notif)
        await self.db.commit()

    async def get_unread_count(self, uuid_user: UUID) -> int:
        return await self.notif_repo.get_unread_count(uuid_user=uuid_user)

    async def get_notifications(
            self,
            uuid_user: UUID,
            pagination: PaginationSchema
        ) -> list[ResponseAllNotifSchema]:
        result = await self.notif_repo.get_notifications(
            uuid_user = uuid_user,
            pagination = pagination
        )
        return [ResponseAllNotifSchema.model_validate(elem) for elem in result]


async def get_notification_service(db: DbDep) -> NotificationService:
    return NotificationService(db=db)

NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]


@router.get("/count")
async def get_unread_count(
    notif_serv: NotificationServiceDep,
    payload = Depends(is_validity_token)
) -> int:
    uuid_user = payload.get("uuid")
    return await notif_serv.get_unread_count(uuid_user=uuid_user)


@router.get("/all")
async def get_notification(
    notif_serv: NotificationServiceDep,
    pagination: PaginationSchema = Depends(),
    payload = Depends(is_validity_token)
) -> list[ResponseAllNotifSchema]:
    uuid_user = payload.get("uuid")
    return await notif_serv.get_notifications(uuid_user=uuid_user, pagination=pagination)


@router.patch("/update")
async def update_read_notification(
    req_update_notif: UpdateNotifSchema,
    notif_serv: NotificationServiceDep,
    payload = Depends(is_validity_token)
) -> None:
    uuid_user = payload.get("uuid")
    await notif_serv.update_read_notification(uuid_user=uuid_user, req_update_notif=req_update_notif)