# Docker lifecycle: build the image, start a seeded container, wait for it
# to become healthy, and (on success only) tear everything down again.

IMAGE_NAME="sillysite-test"
CONTAINER_NAME="sillysite-test"
DB_NAME_TEST="sillysite"
# Which container db_set_config/db_get_config target. Defaults to the full
# suite's container; fast_check.sh points this at the fastdb container
# instead after sourcing lib/fastdb.sh.
DB_CONTAINER="$CONTAINER_NAME"

preflight_checks() {
    local missing=()
    for bin in docker curl python3 node make cc chromedriver javac java; do
        command -v "$bin" >/dev/null 2>&1 || missing+=("$bin")
    done
    if [ "${#missing[@]}" -gt 0 ]; then
        echo "Missing required tools: ${missing[*]}" >&2
        exit 2
    fi
    if ! docker info >/dev/null 2>&1; then
        echo "Docker daemon is not reachable (is it running? do you have permission?)" >&2
        exit 2
    fi
}

# own_container_network
# If this script is itself running inside a Docker container (the
# .devcontainer "app" service, detected via /.dockerenv) that talks to the
# *host's* dockerd over a bind-mounted socket (Docker-outside-of-Docker),
# prints the name of a docker network this container is attached to and
# returns 0. A container we start published only to the host's loopback
# (-p 127.0.0.1:PORT:...) is unreachable from here, since we're in our own
# network namespace, separate from the host's -- so callers use this to
# decide whether to instead attach sidecar containers to this same network
# and address them by container name. Prints nothing and returns 1 when not
# in a container (plain host run), where 127.0.0.1 + published port already
# works and needs no special handling.
own_container_network() {
    [ -f /.dockerenv ] || return 1
    docker inspect "$(hostname)" 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(next(iter(data[0]["NetworkSettings"]["Networks"])))
except Exception:
    sys.exit(1)
'
}

# find_free_port <start>
# Picks the first free TCP port at or after <start> (checked against both
# IPv4 and IPv6 loopback listeners).
find_free_port() {
    local port="$1"
    while ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE "[.:]$port\$"; do
        port=$((port + 1))
    done
    echo "$port"
}

check_no_leftover_container() {
    if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        cat >&2 <<EOF
ERROR: a container named '$CONTAINER_NAME' already exists.

This is most likely left over from a previous test run that failed (the
suite intentionally keeps Docker objects around on failure for post-mortem
inspection). Inspect it, then remove it before re-running:

  docker logs $CONTAINER_NAME
  docker rm -f -v $CONTAINER_NAME
  docker rmi $IMAGE_NAME   # optional, only if you want to force a clean rebuild
EOF
        exit 1
    fi
}

build_image() {
    echo "Building Docker image '$IMAGE_NAME' (this may take a while on first run)..."
    if ! docker build -t "$IMAGE_NAME" "$PROJECT_ROOT" > "$TESTS_DIR/build.log" 2>&1; then
        echo "Docker build failed. See tests/build.log" >&2
        tail -n 40 "$TESTS_DIR/build.log" >&2
        exit 1
    fi
}

start_container() {
    echo "Starting container '$CONTAINER_NAME' (reachable at $BASE_URL)..."
    local network_args=()
    if [ -n "${CONTAINER_NETWORK:-}" ]; then
        network_args=(--network "$CONTAINER_NETWORK")
    fi
    docker run -d \
        --name "$CONTAINER_NAME" \
        "${network_args[@]}" \
        -p "127.0.0.1:${TEST_PORT}:8000" \
        -e "API_KEY=${ADMIN_KEY}" \
        -e "SEED_DB=true" \
        "$IMAGE_NAME" > /dev/null
}

wait_for_healthy() {
    echo "Waiting for the API to come up and finish seeding..."
    local deadline=$((SECONDS + 120))
    while [ "$SECONDS" -lt "$deadline" ]; do
        local code
        code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/about" 2>/dev/null || true)"
        if [ "$code" = "200" ]; then
            # /about is up; confirm seeding finished by checking a known season.
            code="$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-Key: $ADMIN_KEY" "$BASE_URL/season/2014" 2>/dev/null || true)"
            if [ "$code" = "200" ]; then
                echo "API is up and seeded."
                return 0
            fi
        fi
        if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
            echo "Container '$CONTAINER_NAME' exited unexpectedly. Logs:" >&2
            docker logs "$CONTAINER_NAME" >&2 2>&1 || true
            exit 1
        fi
        sleep 1
    done
    echo "Timed out waiting for the API to become healthy." >&2
    docker logs "$CONTAINER_NAME" >&2 2>&1 || true
    exit 1
}

# db_set_config <key> <value>
db_set_config() {
    docker exec "$DB_CONTAINER" gosu postgres psql -d "$DB_NAME_TEST" -c \
        "UPDATE app_config SET value='$2' WHERE key='$1';" > /dev/null
}

# db_get_config <key>
db_get_config() {
    docker exec "$DB_CONTAINER" gosu postgres psql -d "$DB_NAME_TEST" -t -A -c \
        "SELECT value FROM app_config WHERE key='$1';"
}

cleanup_docker() {
    echo "Cleaning up Docker objects..."
    docker rm -f -v "$CONTAINER_NAME" > /dev/null 2>&1 || true
    docker rmi "$IMAGE_NAME" > /dev/null 2>&1 || true
}

print_postmortem_info() {
    cat <<EOF

Docker objects were left running for post-mortem inspection:
  Container: $CONTAINER_NAME  (API at ${BASE_URL}/)
  Image:     $IMAGE_NAME

  docker logs $CONTAINER_NAME
  docker exec -it $CONTAINER_NAME bash

When done, clean up manually with:
  docker rm -f -v $CONTAINER_NAME
  docker rmi $IMAGE_NAME
EOF
}
