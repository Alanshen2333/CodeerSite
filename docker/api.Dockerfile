FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src/api

RUN groupadd --system --gid 10001 codeersite \
    && useradd --system --uid 10001 --gid codeersite --home-dir /app codeersite

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir .

COPY alembic.ini ./
COPY src/api ./src/api
RUN chown -R codeersite:codeersite /app

USER codeersite
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "60", "--no-control-socket", "--access-logfile", "-", "--error-logfile", "-", "src.api.wsgi:app"]
