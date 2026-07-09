FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==2.4.1
COPY srv_auth/pyproject.toml srv_auth/poetry.lock ./srv_auth/
COPY core_app ./core_app
COPY srv_auth/src ./srv_auth/src
WORKDIR /app/srv_auth
RUN poetry install --only main --no-root
ENV PYTHONPATH=/app
CMD ["uvicorn", "srv_auth.src.main:app", "--host", "0.0.0.0", "--port", "8001"]