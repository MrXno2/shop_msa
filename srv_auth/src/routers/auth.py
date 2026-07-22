from datetime import datetime, timedelta, timezone
import re
from typing import Annotated
from uuid import UUID
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
import jwt
from pydantic import BaseModel, Field, field_validator, model_validator
import core_app.security as security
from core_app.exception import InvalidPassword, UserEmailAlreadyExists, UserNotFound, UserPhoneAlreadyExists
from core_app.settings import settings
from srv_auth.src.db.models.user import UserORM
from srv_auth.src.dependensies import DbDep
from sqlalchemy.exc import IntegrityError
from srv_auth.src.rabbit.rabbit import rabbit_wallet_user


# хэширует пароль
def hashed_pass(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")  # ← возвращаем строку


# проверка пароля
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8"),  # ← превращаем строку в байты
    )


router = APIRouter(prefix="/auth")


class AuthLoginReqSchema(BaseModel):
    number: str = Field(min_length=4, max_length=30, description="Number phone")
    password: str = Field(min_length=6, max_length=100, description="Password")

    @field_validator("number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        
        if not re.match(r"^\+\d{10,15}$", cleaned):
            raise ValueError("Phone must be in international format: +79991234567")
        return cleaned
    

class AuthLoginAdminReqSchema(BaseModel):
    login: str = Field(min_length=4, max_length=100, description="Login user")
    password: str = Field(min_length=4, max_length=100, description="Password")
    

class AuthRegisterReqSchema(BaseModel):
    number: str = Field(min_length=4, max_length=30, description="Number phone")
    password1: str = Field(min_length=6, max_length=100, pattern=r"^\S+$", description="Password")
    password2: str = Field(min_length=6, max_length=100, pattern=r"^\S+$", description="Password")
    email: str = Field(max_length=255)
    country: str = Field(max_length=155)
    city: str = Field(max_length=155)
    address: str = Field(max_length=255)

    @field_validator("number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Убираем пробелы, дефисы, скобки
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        
        # Проверяем международный формат: + и цифры
        if not re.match(r"^\+\d{10,15}$", cleaned):
            raise ValueError("Phone must be in international format: +79991234567")
        return cleaned
    
    @model_validator(mode="after")
    def check_password(self):
        if self.password1 != self.password2:
            raise ValueError("Passwords do not match.")
        return self
    

class UserDataWalletSchema(BaseModel):
    uuid: UUID
    number: str


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db


    async def create_user(self, new_user: UserORM) -> str | None:
        try:
            self.db.add(new_user)
            await self.db.flush()
        except IntegrityError as err:
            if "ix_users_number" in str(err.orig):
                raise UserPhoneAlreadyExists()
            if "users_email_key" in str(err.orig):
                raise UserEmailAlreadyExists()
            raise


    async def get_user(self, number: str) -> UserORM | None:
        user = await self.db.execute(
            select(UserORM)
            .where(UserORM.number == number)
            .limit(1)
        )
        return user.scalar_one_or_none()
    

class AuthService():
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.auth_repo = UserRepository(db)

    async def register_user(self, req_data: AuthRegisterReqSchema) -> str | None:
        new_user = UserORM(
            number = req_data.number,
            password_hash = hashed_pass(req_data.password1),
            email = req_data.email,
            country = req_data.country,
            city = req_data.city,
            address = req_data.address
        )
        try:
            # запрос в бд
            await self.auth_repo.create_user(new_user)
            await self.db.commit()
            event = UserDataWalletSchema.model_validate(new_user)
            await rabbit_wallet_user.publish("payment_auth.created", event.model_dump(mode="json"))
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



async def get_auth_servise(db: DbDep) -> AuthService:
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_servise)]


@router.post("/login", status_code=status.HTTP_200_OK)
async def auth_login_user(
    req_data: AuthLoginReqSchema,
    response: Response,
    auth_service: AuthServiceDep
) -> None:
    uuid_user = await auth_service.login_user(req_data)
    token = security.create_access_token({"uuid": uuid_user, "role": "user"})
    security.set_cookie("access_token", response, token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def auth_register_user(
    req_data: AuthRegisterReqSchema,
    auth_service: AuthServiceDep,
    response: Response
):
    uuid_user = await auth_service.register_user(req_data)
    token = security.create_access_token({"uuid": uuid_user})
    security.set_cookie("access_token", response, token)
    return token


@router.post("/login_admin", status_code=status.HTTP_200_OK)
async def auth_login_admin(
    req_data: AuthLoginAdminReqSchema,
    response: Response,
    auth_service: AuthServiceDep
) -> None:
    await auth_service.login_admin(req_data)
    token = security.create_access_token({"uuid": "admin"})
    security.set_cookie("admin_access_token", response, token)


@router.get("/me")
async def me_user(payload = Depends(security.is_validity_token)):
    return payload.get("uuid")


@router.get("/me_admin")
async def me_admin(payload = Depends(security.is_admin_token)):
   return payload.get("uuid")