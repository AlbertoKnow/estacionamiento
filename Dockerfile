FROM python:3.12-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

FROM base as dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM dependencies as production

RUN useradd --create-home --shell /bin/bash appuser

COPY --chown=appuser:appuser . .

COPY --chown=appuser:appuser scripts/entrypoint.prod.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
