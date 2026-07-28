from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core_app.exception import UserEmailAlreadyExists, UserPhoneAlreadyExists
from srv_auth.src.db.models.user import UserORM


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, new_user: UserORM) -> str | None:
        try:
            self.db.add(new_user)
            await self.db.flush()
        except IntegrityError as err:
            if "ix_users_number" in str(err.orig):
                raise UserPhoneAlreadyExists() from None
            if "users_email_key" in str(err.orig):
                raise UserEmailAlreadyExists() from None
            raise

    async def get_user(self, number: str) -> UserORM | None:
        user = await self.db.execute(select(UserORM).where(UserORM.number == number).limit(1))
        return user.scalar_one_or_none()
