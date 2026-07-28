import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class RabbitAuthCreatedEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid_user: UUID
    number: str
