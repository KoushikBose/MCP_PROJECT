# syntax=docker/dockerfile:1.7
#
# Builds one image that serves all three ClinInsight AI entry points
# (FastAPI backend, Streamlit dashboard, stdio MCP server) — see
# docker-compose.yml for how each is started from it via `command:`.

########################################################################
# Builder — resolve dependencies with uv from the committed lockfile
########################################################################
FROM python:3.12-slim-bookworm AS builder

# Official static uv/uvx binaries — no separate installer step needed.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Install deps first so this layer is cached until pyproject.toml/uv.lock change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Application source (this project has no separate package — files live at repo root).
COPY app.py mcp_tool.py ./
COPY functions/ ./functions/
COPY ui/ ./ui/

########################################################################
# Runtime — slim image, no build toolchain, non-root user
########################################################################
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CLINISIGHT_CACHE_DIR=/app/.cache/clinisight

RUN mkdir -p /app/.cache/clinisight && chown -R app:app /app/.cache

USER app

EXPOSE 8081 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8081/ || exit 1

# Default target: the FastAPI backend. docker-compose.yml overrides `command`
# for the Streamlit UI and the stdio MCP server, which reuse this same image.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "2"]
