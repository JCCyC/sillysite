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

# --- TLS: resolve a server certificate, or generate a self-signed one ---
#
# TLS_CERT_FILE/TLS_KEY_FILE are only exported (and the API only serves
# HTTPS) when TLS_ENABLED=true -- the test suite's containers never set
# this, so they keep getting plain HTTP with no changes needed there.
# docker/deploy.sh (the production deployment path this was added for)
# defaults it on.
if [ "${TLS_ENABLED:-false}" = "true" ] || [ "${TLS_ENABLED:-false}" = "yes" ]; then
    TLS_DIR="$STATE_DIR/tls"
    mkdir -p "$TLS_DIR"
    CERT_FILE="$TLS_DIR/cert.pem"
    KEY_FILE="$TLS_DIR/key.pem"

    # If deploy.sh bind-mounted a real certificate, install it -- this is
    # checked (and (re)installed) on every start, not just when no
    # certificate exists yet, so swapping in a renewed certificate is just
    # "replace the mounted files and restart the container". This is the
    # opposite of secrets.env's persisted-value-always-wins rule above,
    # because unlike a DB password, a certificate is expected to be
    # rotated over its lifetime.
    PROVIDED_CERT_FILE="/run/sillysite-tls/cert.pem"
    PROVIDED_KEY_FILE="/run/sillysite-tls/key.pem"
    if [ -f "$PROVIDED_CERT_FILE" ] && [ -f "$PROVIDED_KEY_FILE" ]; then
        echo "[entrypoint] Installing the provided TLS certificate"
        cp "$PROVIDED_CERT_FILE" "$CERT_FILE"
        cp "$PROVIDED_KEY_FILE" "$KEY_FILE"
    elif [ -f "$PROVIDED_CERT_FILE" ] || [ -f "$PROVIDED_KEY_FILE" ]; then
        echo "[entrypoint] Both TLS_CERT_FILE and TLS_KEY_FILE must be set together (only one was provided)" >&2
        exit 1
    elif [ ! -s "$CERT_FILE" ] || [ ! -s "$KEY_FILE" ]; then
        echo "[entrypoint] Generating a self-signed TLS certificate (100-year expiry)"
        SAN="DNS:localhost,IP:127.0.0.1"
        CN="localhost"
        if [ -n "${TLS_HOSTNAME:-}" ]; then
            CN="$TLS_HOSTNAME"
            if [[ "$TLS_HOSTNAME" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                SAN="$SAN,IP:$TLS_HOSTNAME"
            else
                SAN="$SAN,DNS:$TLS_HOSTNAME"
            fi
        fi
        openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout "$KEY_FILE" -out "$CERT_FILE" \
            -days 36500 \
            -subj "/CN=$CN" \
            -addext "subjectAltName=$SAN" \
            >/dev/null 2>&1
    else
        echo "[entrypoint] Using existing TLS certificate at $CERT_FILE"
    fi

    chown appuser:appuser "$CERT_FILE" "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"

    export TLS_CERT_FILE="$CERT_FILE"
    export TLS_KEY_FILE="$KEY_FILE"
fi

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
