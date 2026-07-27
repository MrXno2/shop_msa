# CI / TEST
FROM python:3.12-slim AS test
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1

COPY srv_payment/pyproject.toml srv_payment/poetry.lock ./srv_payment/
COPY core_app ./core_app

COPY srv_payment/src ./srv_payment/src
COPY srv_payment/tests ./srv_payment/tests
COPY srv_payment/alembic.ini ./srv_payment/
COPY srv_payment/alembic ./srv_payment/alembic

WORKDIR /app/srv_payment
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

COPY srv_payment/pyproject.toml srv_payment/poetry.lock ./srv_payment/
COPY core_app ./core_app

COPY srv_payment/src ./srv_payment/src
COPY srv_payment/alembic.ini ./srv_payment/
COPY srv_payment/alembic ./srv_payment/alembic

WORKDIR /app/srv_payment
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app

CMD ["sh", "-c", "alembic -c /app/srv_payment/alembic.ini upgrade head && uvicorn srv_payment.src.main:app --host 0.0.0.0 --port 8004"]