from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core_app.settings import settings


def set_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,  # Каким сайтам разрешено, домены / IP
        allow_methods=["*"],  # Какие методы разрешены, CRUD запросы точнее
        allow_headers=["*"],  # Какие заголовки разрешены, CRUD запросов
        allow_credentials=True,  # Можно ли передавать куки/токены
        expose_headers=["*"],  # Какие заголовки видны фронту
        max_age=600,  # Как долго кешировать CORS (в секундах)
    )
