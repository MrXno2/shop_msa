FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1
COPY srv_notification/pyproject.toml srv_notification/poetry.lock ./srv_notification/
COPY srv_notification ./srv_notification
COPY srv_notification/src ./srv_notification/src
WORKDIR /app/srv_notification
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app
CMD ["uvicorn", "srv_notification.src.main:app", "--host", "0.0.0.0", "--port", "8005"]