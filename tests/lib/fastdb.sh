# Lifecycle for a persistent, reused Postgres-only container backing the
# fast test check (tests/fast_check.sh). Unlike the full suite's container
# (always built and torn down fresh), this one stays running across many
# checks to avoid paying the seed-data cost every time -- only Postgres
# runs here; the API itself runs natively from the current source tree
# (see fast_check.sh), so code edits are reflected with no rebuild at all.
#
# Reuses the same image (and therefore the same entrypoint.sh init/seed
# logic) as the full suite, just with the container's command overridden
# to start Postgres directly instead of supervisord/gunicorn.

FASTDB_CONTAINER="sillysite-fastdb"
FASTDB_PORT_FILE="$TESTS_DIR/.fastdb_port"

# ensure_fastdb_running
# Sets $FASTDB_PORT (host-published port, kept for a plain host run or for
# poking at the container from a host shell) and $FASTDB_HOST/$FASTDB_DB_PORT
# (what to actually set DB_HOST/DB_PORT to -- see own_container_network in
# lib/docker.sh for why these differ when fast_check.sh itself runs inside
# the .devcontainer "app" service). Builds the image and starts (seeded) the
# container if it isn't already running; otherwise reuses it as-is.
ensure_fastdb_running() {
    CONTAINER_NETWORK="$(own_container_network || true)"
    if [ -n "$CONTAINER_NETWORK" ]; then
        FASTDB_HOST="$FASTDB_CONTAINER"
        FASTDB_DB_PORT=5432
    else
        FASTDB_HOST=127.0.0.1
    fi

    if docker ps --format '{{.Names}}' | grep -qx "$FASTDB_CONTAINER" && [ -f "$FASTDB_PORT_FILE" ]; then
        FASTDB_PORT="$(cat "$FASTDB_PORT_FILE")"
        [ -n "$CONTAINER_NETWORK" ] || FASTDB_DB_PORT="$FASTDB_PORT"
        return 0
    fi

    docker rm -f "$FASTDB_CONTAINER" > /dev/null 2>&1 || true

    if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
        build_image
    fi

    FASTDB_PORT="$(find_free_port 19800)"
    echo "$FASTDB_PORT" > "$FASTDB_PORT_FILE"
    [ -n "$CONTAINER_NETWORK" ] || FASTDB_DB_PORT="$FASTDB_PORT"

    local network_args=()
    if [ -n "$CONTAINER_NETWORK" ]; then
        network_args=(--network "$CONTAINER_NETWORK")
    fi

    docker run -d --name "$FASTDB_CONTAINER" \
        "${network_args[@]}" \
        -p "127.0.0.1:${FASTDB_PORT}:5432" \
        -e "API_KEY=unused" \
        -e "SEED_DB=true" \
        "$IMAGE_NAME" \
        bash -c 'exec gosu postgres "$PG_BIN/postgres" -D "$PGDATA"' > /dev/null

    # entrypoint.sh briefly runs its own temporary Postgres instance during
    # init/seed before stopping it and handing off to the command above --
    # pg_isready can succeed against that one moments before it shuts down.
    # Require two consecutive successes, a beat apart, before trusting it.
    local consecutive_ok=0
    local deadline=$((SECONDS + 90))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if pg_isready -h "$FASTDB_HOST" -p "$FASTDB_DB_PORT" > /dev/null 2>&1; then
            consecutive_ok=$((consecutive_ok + 1))
            if [ "$consecutive_ok" -ge 2 ]; then
                return 0
            fi
        else
            consecutive_ok=0
        fi
        if ! docker ps --format '{{.Names}}' | grep -qx "$FASTDB_CONTAINER"; then
            echo "fastdb container exited unexpectedly. Logs:" >&2
            docker logs "$FASTDB_CONTAINER" >&2 2>&1 || true
            return 1
        fi
        sleep 1
    done
    echo "Timed out waiting for fastdb Postgres to come up." >&2
    return 1
}

# fastdb_password
# Prints the DB_PASSWORD generated for the fastdb container.
fastdb_password() {
    docker exec "$FASTDB_CONTAINER" sh -c 'grep "^DB_PASSWORD=" /var/lib/sillysite/secrets.env' | cut -d= -f2
}
