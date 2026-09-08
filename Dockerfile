# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13


FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install production dependencies first to maximize Docker layer caching.
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --locked \
        --no-dev \
        --no-install-project

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 expense-api \
    && useradd \
        --system \
        --uid 10001 \
        --gid expense-api \
        --no-create-home \
        --shell /usr/sbin/nologin \
        expense-api

WORKDIR /app

COPY --from=builder --chown=expense-api:expense-api /opt/venv /opt/venv
COPY --chown=expense-api:expense-api src /app/src
COPY --chown=expense-api:expense-api alembic /app/alembic
COPY --chown=expense-api:expense-api alembic.ini /app/alembic.ini

USER expense-api

EXPOSE 8000

CMD ["uvicorn", "expense_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
