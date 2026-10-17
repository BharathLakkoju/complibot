# API and worker share this image; override CMD in compose or ECS.
FROM python:3.12-slim AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv==0.5.11

COPY pyproject.toml uv.lock README.md ./
COPY packages/ packages/
COPY apps/ apps/
COPY ai/frameworks/ ai/frameworks/
COPY ai/rules/ ai/rules/
COPY database/ database/

RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin complibot \
    && chown -R complibot:complibot /app

ENV PYTHONPATH=/app/packages/complibot/src
ENV PATH="/app/.venv/bin:${PATH}"

USER complibot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
