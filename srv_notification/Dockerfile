# CI / TEST
FROM python:3.12-slim AS test
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1

COPY srv_notification/pyproject.toml srv_notification/poetry.lock ./srv_notification/
COPY core_app ./core_app

COPY srv_notification/src ./srv_notification/src
COPY srv_notification/tests ./srv_notification/tests
COPY srv_notification/alembic.ini ./srv_notification/
COPY srv_notification/alembic ./srv_notification/alembic

WORKDIR /app/srv_notification
RUN poetry install --no-root
ENV PYTHONPATH=/app


# PROD
FROM python:3.12-slim AS production
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1

COPY srv_notification/pyproject.toml srv_notification/poetry.lock ./srv_notification/
COPY core_app ./core_app

COPY srv_notification/src ./srv_notification/src
COPY srv_notification/alembic.ini ./srv_notification/
COPY srv_notification/alembic ./srv_notification/alembic

WORKDIR /app/srv_notification
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app

CMD ["sh", "-c", "alembic -c /app/srv_notification/alembic.ini upgrade head && uvicorn srv_notification.src.main:app --host 0.0.0.0 --port 8005"]