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

