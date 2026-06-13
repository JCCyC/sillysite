#!/bin/bash
set -euo pipefail

export PATH="${PG_BIN}:$PATH"

LIMIT_MB="${DB_SIZE_LIMIT_MB:-0}"

if [ "$LIMIT_MB" -le 0 ]; then
    echo "[db-size-monitor] No DB_SIZE_LIMIT_MB configured; not enforcing a size limit."
    exec sleep infinity
fi

echo "[db-size-monitor] Enforcing a ${LIMIT_MB}MB limit on database \"$DB_NAME\""

while true; do
    sleep 60

    size_mb=$(psql -tA -d "$DB_NAME" -c "SELECT pg_database_size('$DB_NAME') / (1024 * 1024);") || continue
    size_mb=${size_mb//[[:space:]]/}

    if [ "$size_mb" -ge "$LIMIT_MB" ]; then
        psql -d "$DB_NAME" -c "ALTER DATABASE \"$DB_NAME\" SET default_transaction_read_only = on;" >/dev/null
        echo "[db-size-monitor] $DB_NAME is ${size_mb}MB (limit ${LIMIT_MB}MB) - new connections are read-only"
    else
        psql -d "$DB_NAME" -c "ALTER DATABASE \"$DB_NAME\" SET default_transaction_read_only = off;" >/dev/null
    fi
done
