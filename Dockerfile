## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.12-bookworm AS builder

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/0.12.3/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync

## ----------------------------- Production Stage ----------------------------- ##
FROM python:3.12-slim-bookworm AS production

RUN useradd --create-home appuser
USER appuser

WORKDIR /app

COPY /src src
COPY --from=builder /app/.venv .venv

ENV PATH="/app/.venv/bin:$PATH"
