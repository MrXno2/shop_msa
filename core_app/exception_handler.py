from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

import core_app.exception as custom_exception


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(custom_exception.UserNotFound)
    async def user_not_found_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "message": "Пользователь не найден.",
                "error_type": "UserNotFound",
            },
        )

    @app.exception_handler(custom_exception.UserEmailAlreadyExists)
    async def user_email_already_exists_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": "Пользователь с таким email уже существует.",
                "error_type": "UserEmailAlreadyExists",
            },
        )

    @app.exception_handler(custom_exception.UserPhoneAlreadyExists)
    async def user_phone_already_exists_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "message": "Пользователь с таким номером уже существует.",
                "error_type": "UserPhoneAlreadyExists",
            },
        )

    @app.exception_handler(custom_exception.InvalidPassword)
    async def invalid_password_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "message": "Не правильный пароль.",
                "error_type": "InvalidPassword",
            },
        )

    @app.exception_handler(custom_exception.NotAdminError)
    async def not_admin_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "message": "Неа, ты не админ, гуляй Уася.",
                "error_type": "NotAdminError",
            },
        )

    @app.exception_handler(custom_exception.ProductNotFound)
    async def product_not_found_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "message": "Товар не найден.",
                "error_type": "ProductNotFound",
            },
        )

    @app.exception_handler(custom_exception.InsufficientFundsError)
    async def insufficient_funds_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "message": "Ошибка: недостаточно средств.",
                "error_type": "InsufficientFundsError",
            },
        )
