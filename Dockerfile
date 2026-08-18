FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install \
    "aiogram>=3.17.0" \
    "sqlalchemy[asyncio]>=2.0.38" \
    "asyncpg>=0.30.0" \
    "alembic>=1.14.1" \
    "redis[hiredis]>=5.2.1" \
    "pydantic-settings>=2.7.1" \
    "structlog>=25.1.0" \
    "regex>=2024.11.6" \
    "pytest>=8.3.4" \
    "pytest-asyncio>=0.25.3" \
    "pytest-mock>=3.14.0" \
    "aiosqlite>=0.20.0"

COPY . .

CMD ["python", "-m", "app.main"]