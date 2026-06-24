#!/bin/bash
# Builds (if needed) and (re)starts the sillysite container.
#
# Usage: ./deploy.sh [path-to-env-file]
#
# Configuration is read from deploy.env (next to this script) by default,
# or from the path given as the first argument. See deploy.env.example for
# the available settings.
set -euo pipefail

cd "$(dirname "$0")"

ENV_FILE="${1:-deploy.env}"
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE"
else
    echo "No $ENV_FILE found; using defaults (see deploy.env.example)." >&2
fi

API_PORT="${API_PORT:-19505}"
EXPOSE_POSTGRES="${EXPOSE_POSTGRES:-no}"
POSTGRES_PORT="${POSTGRES_PORT:-55432}"
MEMORY_LIMIT="${MEMORY_LIMIT:-1g}"
CPU_LIMIT="${CPU_LIMIT:-1.0}"
DB_SIZE_LIMIT_MB="${DB_SIZE_LIMIT_MB:-0}"
IMAGE_NAME="${IMAGE_NAME:-sillysite}"
CONTAINER_NAME="${CONTAINER_NAME:-sillysite}"
TLS_ENABLED="${TLS_ENABLED:-yes}"
TLS_HOSTNAME="${TLS_HOSTNAME:-}"
TLS_CERT_FILE="${TLS_CERT_FILE:-}"
TLS_KEY_FILE="${TLS_KEY_FILE:-}"

echo "Building image $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" ..

PORT_ARGS=(-p "${API_PORT}:8000")
if [ "$EXPOSE_POSTGRES" = "yes" ] || [ "$EXPOSE_POSTGRES" = "true" ]; then
    PORT_ARGS+=(-p "${POSTGRES_PORT}:5432")
    echo "PostgreSQL will be exposed on host port $POSTGRES_PORT"
else
    echo "PostgreSQL will not be exposed on the host"
fi

ENV_ARGS=(-e "DB_SIZE_LIMIT_MB=${DB_SIZE_LIMIT_MB}" -e "TLS_ENABLED=${TLS_ENABLED}")
for var in DB_NAME DB_USER DB_PASSWORD API_KEY WEB_CONCURRENCY SEED_DB TLS_HOSTNAME; do
    if [ -n "${!var:-}" ]; then
        ENV_ARGS+=(-e "${var}=${!var}")
    fi
done

# TLS_CERT_FILE/TLS_KEY_FILE here are HOST paths to an existing certificate
# (e.g. a real one issued by a CA) -- if both are set, bind-mount them in
# read-only for entrypoint.sh to install; leave both unset to get a
# self-signed certificate generated automatically instead.
MOUNT_ARGS=()
if [ -n "$TLS_CERT_FILE" ] && [ -n "$TLS_KEY_FILE" ]; then
    for f in "$TLS_CERT_FILE" "$TLS_KEY_FILE"; do
        if [ ! -f "$f" ]; then
            echo "TLS_CERT_FILE/TLS_KEY_FILE: $f does not exist" >&2
            exit 1
        fi
    done
    MOUNT_ARGS+=(
        -v "$(readlink -f "$TLS_CERT_FILE"):/run/sillysite-tls/cert.pem:ro"
        -v "$(readlink -f "$TLS_KEY_FILE"):/run/sillysite-tls/key.pem:ro"
    )
    echo "Using the provided TLS certificate ($TLS_CERT_FILE)"
elif [ -n "$TLS_CERT_FILE" ] || [ -n "$TLS_KEY_FILE" ]; then
    echo "TLS_CERT_FILE and TLS_KEY_FILE must both be set together (only one was set)" >&2
    exit 1
elif [ "$TLS_ENABLED" = "yes" ] || [ "$TLS_ENABLED" = "true" ]; then
    echo "No TLS_CERT_FILE/TLS_KEY_FILE set; a self-signed certificate will be generated"
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "Removing existing container $CONTAINER_NAME..."
    docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker volume create "${CONTAINER_NAME}_pgdata" >/dev/null
docker volume create "${CONTAINER_NAME}_state" >/dev/null

echo "Starting container $CONTAINER_NAME..."
RUN_ARGS=(-d
    --name "$CONTAINER_NAME"
    --restart unless-stopped
    --memory "$MEMORY_LIMIT"
    "${PORT_ARGS[@]}"
    "${ENV_ARGS[@]}"
    "${MOUNT_ARGS[@]}"
    -v "${CONTAINER_NAME}_pgdata:/var/lib/postgresql/data"
    -v "${CONTAINER_NAME}_state:/var/lib/sillysite"
)

if ! docker run "${RUN_ARGS[@]}" --cpus "$CPU_LIMIT" "$IMAGE_NAME" 2>/tmp/sillysite-run.err; then
    if grep -qi "NanoCPUs can not be set" /tmp/sillysite-run.err; then
        echo "Warning: this host's kernel doesn't support CPU limits (--cpus); starting without one." >&2
        docker run "${RUN_ARGS[@]}" "$IMAGE_NAME"
    else
        cat /tmp/sillysite-run.err >&2
        rm -f /tmp/sillysite-run.err
        exit 1
    fi
fi
rm -f /tmp/sillysite-run.err

if [ "$TLS_ENABLED" = "yes" ] || [ "$TLS_ENABLED" = "true" ]; then
    SCHEME=https
else
    SCHEME=http
fi

echo
echo "Container started. The API is available at ${SCHEME}://127.0.0.1:${API_PORT}/"
if [ "$SCHEME" = "https" ] && [ -z "$TLS_CERT_FILE" ]; then
    echo "Using a self-signed certificate -- clients will need to ignore/trust it manually" \
         "(e.g. curl -k, or import $CONTAINER_NAME's cert.pem as a trusted CA)."
fi
echo "To retrieve the generated API key (if you didn't set one), run:"
echo "  docker exec $CONTAINER_NAME cat /var/lib/sillysite/secrets.env"
if [ "$SCHEME" = "https" ]; then
    echo "To retrieve the certificate (e.g. to import it as a trusted CA), run:"
    echo "  docker exec $CONTAINER_NAME cat /var/lib/sillysite/tls/cert.pem"
fi
echo "To follow logs:"
echo "  docker logs -f $CONTAINER_NAME"
