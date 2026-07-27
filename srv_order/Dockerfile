# CI / TEST
FROM python:3.12-slim AS test
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1

COPY srv_order/pyproject.toml srv_order/poetry.lock ./srv_order/
COPY core_app ./core_app

COPY srv_order/src ./srv_order/src
COPY srv_order/tests ./srv_order/tests
COPY srv_order/alembic.ini ./srv_order/
COPY srv_order/alembic ./srv_order/alembic

WORKDIR /app/srv_order
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

COPY srv_order/pyproject.toml srv_order/poetry.lock ./srv_order/
COPY core_app ./core_app

COPY srv_order/src ./srv_order/src
COPY srv_order/alembic.ini ./srv_order/
COPY srv_order/alembic ./srv_order/alembic

WORKDIR /app/srv_order
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app

CMD ["sh", "-c", "alembic -c /app/srv_order/alembic.ini upgrade head && uvicorn srv_order.src.main:app --host 0.0.0.0 --port 8003"]