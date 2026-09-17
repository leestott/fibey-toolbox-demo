FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
COPY server.py ./
COPY data/ ./data/

RUN uv sync --frozen --no-dev

EXPOSE 8002

RUN useradd --uid 10001 --create-home appuser
USER appuser

CMD ["/app/.venv/bin/python", "server.py"]
