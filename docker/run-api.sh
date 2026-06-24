#!/bin/bash
# supervisord's "api" program entry point. Split out from a one-line
# command= (as db-size-monitor.sh already is) once the TLS conditional made
# a single supervisord.conf line unwieldy.
set -euo pipefail

until pg_isready -h 127.0.0.1 -q; do
    sleep 1
done

# TLS_CERT_FILE/TLS_KEY_FILE are only set (by entrypoint.sh, when
# TLS_ENABLED=true) once a certificate has been resolved or generated --
# their absence here means TLS is off and gunicorn serves plain HTTP.
TLS_ARGS=()
if [ -n "${TLS_CERT_FILE:-}" ] && [ -n "${TLS_KEY_FILE:-}" ]; then
    TLS_ARGS=(--certfile "$TLS_CERT_FILE" --keyfile "$TLS_KEY_FILE")
fi

exec /app/.venv/bin/gunicorn main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 \
    -w "$WEB_CONCURRENCY" "${TLS_ARGS[@]}" --access-logfile - --error-logfile -
