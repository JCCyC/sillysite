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

echo "Building image $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" ..

PORT_ARGS=(-p "${API_PORT}:8000")
if [ "$EXPOSE_POSTGRES" = "yes" ] || [ "$EXPOSE_POSTGRES" = "true" ]; then
    PORT_ARGS+=(-p "${POSTGRES_PORT}:5432")
    echo "PostgreSQL will be exposed on host port $POSTGRES_PORT"
else
    echo "PostgreSQL will not be exposed on the host"
fi

ENV_ARGS=(-e "DB_SIZE_LIMIT_MB=${DB_SIZE_LIMIT_MB}")
for var in DB_NAME DB_USER DB_PASSWORD API_KEY WEB_CONCURRENCY SEED_DB; do
    if [ -n "${!var:-}" ]; then
        ENV_ARGS+=(-e "${var}=${!var}")
    fi
done

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

echo
echo "Container started. The API is available at http://127.0.0.1:${API_PORT}/"
echo "To retrieve the generated API key (if you didn't set one), run:"
echo "  docker exec $CONTAINER_NAME cat /var/lib/sillysite/secrets.env"
echo "To follow logs:"
echo "  docker logs -f $CONTAINER_NAME"
