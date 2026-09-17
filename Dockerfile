FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt ./
RUN uv pip install --system --no-deps -r requirements.txt

COPY src/fibey/gateway/ ./src/fibey/gateway/
COPY src/fibey/__init__.py ./src/fibey/__init__.py

RUN useradd --create-home --uid 10001 fibey

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER fibey

EXPOSE 8000

CMD ["uvicorn", "fibey.gateway.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
