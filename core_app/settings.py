from datetime import timedelta
from pathlib import Path
#from authx.types import TokenLocation
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# нужно установить прямой путь к корню проекта и передавать в env
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )

    PROJECT_NAME: str = "my-project"

    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    JWT_SECRET_KEY: str = "dopustim_pass_very_secret_key"
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS: int = 36000

    RABBIT_URL: str = "amqp://guest:guest@localhost:5672/"

    # db localhost
    POSTGRES_URL_SERV_AUTH: str = "postgresql+asyncpg://postgres:admin@localhost:5432/postgres"
    POSTGRES_URL_SERV_CART: str = "postgresql+asyncpg://postgres:admin@localhost:5432/postgres"
    POSTGRES_URL_SERV_CATALOG: str = "postgresql+asyncpg://postgres:admin@localhost:5432/postgres"

    ADMIN_PANEL_USER: str = "admin"
    ADMIN_PANEL_PASSWORD: str = "qwerty"


settings = Settings()
