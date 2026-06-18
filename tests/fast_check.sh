#!/usr/bin/env bash
# Fast, lightweight test check.
#
# Usage: tests/fast_check.sh
#
# Reuses a persistent throwaway Postgres container (sillysite-fastdb,
# created on first use, left running afterward) and runs the API directly
# from the current source tree via the venv's uvicorn -- no Docker image
# rebuild, no reseeding -- against the pure-API test subset only (skips
# the Python-script and C/JS-binding tests, which add subprocess overhead
# and rarely break from typical app-code edits). Writes a report to
# tests/fast_report.txt.
#
# This is NOT a replacement for tests/run_tests.sh, which remains the
# authoritative, full-coverage suite (API + scripts + C/JS bindings,
# against a freshly built and seeded Docker image) -- run that before
# considering a feature done. This script exists to make a quick
# correctness check cheap enough to run after every change.
#
# Note: the fastdb container's data isn't reset between checks, so
# harmless test rows (unique-named per run) accumulate over time. Remove
# it with `docker rm -f -v sillysite-fastdb` to start clean.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TESTS_DIR/.." && pwd)"
REPORT_FILE="$TESTS_DIR/fast_report.txt"

# shellcheck source=lib/framework.sh
source "$TESTS_DIR/lib/framework.sh"
# shellcheck source=lib/docker.sh
source "$TESTS_DIR/lib/docker.sh"
# shellcheck source=lib/fastdb.sh
source "$TESTS_DIR/lib/fastdb.sh"
# shellcheck source=lib/api.sh
source "$TESTS_DIR/lib/api.sh"
# shellcheck source=lib/proc.sh
source "$TESTS_DIR/lib/proc.sh"

for bin in docker curl python3 pg_isready; do
    if ! command -v "$bin" > /dev/null 2>&1; then
        echo "Missing required tool: $bin" >&2
        exit 2
    fi
done
if ! docker info > /dev/null 2>&1; then
    echo "Docker daemon is not reachable" >&2
    exit 2
fi

ensure_fastdb_running || exit 1
DB_CONTAINER="$FASTDB_CONTAINER"

API_PORT="$(find_free_port 19900)"
ADMIN_KEY="fastcheckkey0000000000000000000000000000"
BASE_URL="http://127.0.0.1:${API_PORT}"

export DB_HOST=127.0.0.1
export DB_PORT="$FASTDB_PORT"
export DB_SCHEMA=public
export DB_NAME="$DB_NAME_TEST"
export DB_USER="$DB_NAME_TEST"
export DB_PASSWORD="$(fastdb_password)"
export API_KEY="$ADMIN_KEY"

"$PROJECT_ROOT/.venv/bin/uvicorn" --app-dir "$PROJECT_ROOT" main:app --port "$API_PORT" \
    > "$TESTS_DIR/fast_uvicorn.log" 2>&1 &
UVICORN_PID=$!

cleanup_uvicorn() {
    kill "$UVICORN_PID" > /dev/null 2>&1 || true
    wait "$UVICORN_PID" 2> /dev/null || true
}
trap cleanup_uvicorn EXIT

up=false
deadline=$((SECONDS + 30))
while [ "$SECONDS" -lt "$deadline" ]; do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/about" 2>/dev/null || true)"
    if [ "$code" = "200" ]; then
        up=true
        break
    fi
    if ! kill -0 "$UVICORN_PID" 2> /dev/null; then
        break
    fi
    sleep 0.5
done
if [ "$up" != true ]; then
    echo "API failed to come up. Log:" >&2
    cat "$TESTS_DIR/fast_uvicorn.log" >&2
    exit 1
fi

for case_file in \
    "$TESTS_DIR/cases/10_public.sh" \
    "$TESTS_DIR/cases/20_login.sh" \
    "$TESTS_DIR/cases/30_changepw.sh" \
    "$TESTS_DIR/cases/40_whoami_logout.sh" \
    "$TESTS_DIR/cases/50_users.sh" \
    "$TESTS_DIR/cases/60_business.sh" \
    "$TESTS_DIR/cases/70_config_activeusers.sh"
do
    # shellcheck source=/dev/null
    source "$case_file"
done

run_all_tests

echo "Passed: $PASS_COUNT / ${#TEST_FN[@]}"
echo "Failed: $FAIL_COUNT / ${#TEST_FN[@]}"
echo "Full report: $REPORT_FILE"

[ "$FAIL_COUNT" -eq 0 ]
