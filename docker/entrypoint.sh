#!/bin/bash
set -euo pipefail

PG_BIN="$(find /usr/lib/postgresql -maxdepth 2 -type d -name bin | sort -V | tail -1)"
export PATH="$PG_BIN:$PATH"
export PG_BIN

STATE_DIR="${STATE_DIR:-/var/lib/sillysite}"
SECRETS_FILE="$STATE_DIR/secrets.env"

mkdir -p "$STATE_DIR" "$PGDATA"
chown -R postgres:postgres /var/lib/postgresql
chown -R appuser:appuser "$STATE_DIR"

# Generate (and persist) a DB password and API key on first run, so they
# survive container restarts without the recipient having to set them.
if [ -f "$SECRETS_FILE" ]; then
    # shellcheck disable=SC1090
    source "$SECRETS_FILE"
fi

if [ -z "${DB_PASSWORD:-}" ]; then
    DB_PASSWORD="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32 || true)"
fi
if [ -z "${API_KEY:-}" ]; then
    API_KEY="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 40 || true)"
fi

cat > "$SECRETS_FILE" <<EOF
DB_PASSWORD=$DB_PASSWORD
API_KEY=$API_KEY
EOF
chown appuser:appuser "$SECRETS_FILE"
chmod 600 "$SECRETS_FILE"

export DB_PASSWORD API_KEY

# --- Initialize the PostgreSQL cluster on first run ---
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "[entrypoint] Initializing PostgreSQL data directory at $PGDATA"
    gosu postgres "$PG_BIN/initdb" -D "$PGDATA" --auth-local=trust --auth-host=scram-sha-256 --encoding=UTF8 >/dev/null

    {
        echo "listen_addresses = '*'"
        echo "port = 5432"
    } >> "$PGDATA/postgresql.conf"

    {
        echo "host all all 0.0.0.0/0 scram-sha-256"
        echo "host all all ::/0 scram-sha-256"
    } >> "$PGDATA/pg_hba.conf"

    gosu postgres "$PG_BIN/pg_ctl" -D "$PGDATA" -w start

    gosu postgres psql -v ON_ERROR_STOP=1 -d postgres <<-SQL
        CREATE ROLE "$DB_USER" WITH LOGIN PASSWORD '$DB_PASSWORD';
        CREATE DATABASE "$DB_NAME" OWNER "$DB_USER";
SQL

    if [ "${SEED_DB:-false}" = "true" ]; then
        echo "[entrypoint] Seeding database with sample data"
        gosu appuser /app/.venv/bin/python /app/seed.py
    fi

    gosu postgres "$PG_BIN/pg_ctl" -D "$PGDATA" -m fast -w stop
else
    echo "[entrypoint] Using existing PostgreSQL data directory at $PGDATA"
fi

echo "[entrypoint] API key: $API_KEY"

exec "$@"
