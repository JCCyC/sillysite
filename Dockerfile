FROM debian:stable-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PGDATA=/var/lib/postgresql/data \
    STATE_DIR=/var/lib/sillysite \
    DB_HOST=127.0.0.1 \
    DB_PORT=5432 \
    DB_SCHEMA=public \
    DB_NAME=sillysite \
    DB_USER=sillysite \
    WEB_CONCURRENCY=2 \
    DB_SIZE_LIMIT_MB=0 \
    SEED_DB=false \
    TLS_ENABLED=false \
    TLS_HOSTNAME=

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql \
        python3 \
        python3-venv \
        gosu \
        supervisor \
        openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN useradd --system --create-home --home-dir /home/appuser appuser && \
    mkdir -p "$STATE_DIR" "$PGDATA" && \
    chown -R postgres:postgres /var/lib/postgresql && \
    chown -R appuser:appuser /app "$STATE_DIR"

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/db-size-monitor.sh /usr/local/bin/db-size-monitor.sh
COPY docker/run-api.sh /usr/local/bin/run-api.sh
COPY docker/supervisord.conf /etc/supervisor/conf.d/sillysite.conf
RUN chmod +x /entrypoint.sh /usr/local/bin/db-size-monitor.sh /usr/local/bin/run-api.sh

EXPOSE 8000 5432

VOLUME ["/var/lib/postgresql/data", "/var/lib/sillysite"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/sillysite.conf", "-n"]
