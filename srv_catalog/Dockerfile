# CI / TEST
FROM python:3.12-slim AS test
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1

COPY srv_catalog/pyproject.toml srv_catalog/poetry.lock ./srv_catalog/
COPY core_app ./core_app

COPY srv_catalog/src ./srv_catalog/src
COPY srv_catalog/tests ./srv_catalog/tests
COPY srv_catalog/alembic.ini ./srv_catalog/
COPY srv_catalog/alembic ./srv_catalog/alembic

WORKDIR /app/srv_catalog
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

COPY srv_catalog/pyproject.toml srv_catalog/poetry.lock ./srv_catalog/
COPY core_app ./core_app

COPY srv_catalog/src ./srv_catalog/src
COPY srv_catalog/alembic.ini ./srv_catalog/
COPY srv_catalog/alembic ./srv_catalog/alembic

WORKDIR /app/srv_catalog
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app

CMD ["sh", "-c", "alembic -c /app/srv_catalog/alembic.ini upgrade head && uvicorn srv_catalog.src.main:app --host 0.0.0.0 --port 8002"]