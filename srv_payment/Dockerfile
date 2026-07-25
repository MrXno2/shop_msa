FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1
COPY srv_payment/pyproject.toml srv_payment/poetry.lock ./srv_payment/
COPY core_app ./core_app
COPY srv_payment/src ./srv_payment/src
WORKDIR /app/srv_payment
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app
CMD ["uvicorn", "srv_payment.src.main:app", "--host", "0.0.0.0", "--port", "8004"]