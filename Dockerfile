## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.12-bookworm AS builder

ADD https://astral.sh/uv/0.12.3/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen

## ----------------------------- Production Stage ----------------------------- ##
FROM python:3.12-slim-bookworm AS production

RUN useradd --create-home appuser

WORKDIR /app

RUN mkdir -p /app/storage && chown appuser:appuser /app/storage

COPY --chown=appuser:appuser /src src
COPY --from=builder --chown=appuser:appuser /app/.venv .venv

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/api/v1/health').status==200 else 1)"
