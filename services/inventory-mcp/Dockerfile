FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY server.py ./server.py
COPY data ./data

EXPOSE 8001

RUN useradd --uid 10001 --create-home appuser
USER appuser

CMD ["/app/.venv/bin/python", "server.py"]
