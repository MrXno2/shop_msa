from sqlalchemy.ext.asyncio import AsyncSession

from core_app.exception import InvalidPassword, UserEmailAlreadyExists, UserNotFound, UserPhoneAlreadyExists
from core_app.rabbit import rabbit_payment_auth
from core_app.settings import settings
from srv_auth.src.db.models.user import UserORM
from srv_auth.src.modules.auth.repository import UserRepository
from srv_auth.src.modules.auth.schemas import (
    AuthLoginAdminReqSchema,
    AuthLoginReqSchema,
    AuthRegisterReqSchema,
    RabbitAuthCreatedEventSchema,
)
from srv_auth.src.modules.auth.utils import hashed_pass, verify_password


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth_repo = UserRepository(db)

    async def register_user(self, req_data: AuthRegisterReqSchema) -> str | None:
        new_user = UserORM(
            number=req_data.number,
            password_hash=hashed_pass(req_data.password1),
            email=req_data.email,
            country=req_data.country,
            city=req_data.city,
            address=req_data.address,
        )
        try:
            # запрос в бд
            await self.auth_repo.create_user(new_user)
            await self.db.commit()
            event = RabbitAuthCreatedEventSchema(uuid_user=new_user.uuid, number=new_user.number)
            await rabbit_payment_auth.publish("payment_auth.created", event.model_dump(mode="json"))
            return str(new_user.uuid)
        except (UserPhoneAlreadyExists, UserEmailAlreadyExists):
            await self.db.rollback()
            raise

    async def login_user(self, req_data: AuthLoginReqSchema) -> str | None:
        user = await self.auth_repo.get_user(req_data.number)
        if not user:
            raise UserNotFound()
        if not verify_password(req_data.password, user.password_hash):
            raise InvalidPassword()
        return str(user.uuid)

    async def login_admin(self, req_data: AuthLoginAdminReqSchema) -> None:
        if req_data.login != settings.ADMIN_PANEL_USER:
            raise UserNotFound()
        if req_data.password != settings.ADMIN_PANEL_PASSWORD:
            raise InvalidPassword()
