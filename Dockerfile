FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.4.30 /uv /uvx /usr/local/bin/

WORKDIR /wedding-app

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && chown -R app:app /wedding-app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .
RUN uv sync --locked

ENV UV_CACHE_DIR=/wedding-app/.cache/uv

USER app

EXPOSE 5000

CMD ["uv", "run", "python", "app/main.py"]
