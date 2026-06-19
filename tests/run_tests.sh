#!/usr/bin/env bash
# SillySite test suite.
#
# Usage: tests/run_tests.sh
#
# Builds a fresh Docker image, runs it as a seeded container, and runs the
# full test suite (the HTTP API, the Python/C/JS clients) against it. On
# success, all Docker objects this script created are removed and the exit
# code is 0. On failure, the container and image are left running for
# post-mortem (docker logs / docker exec), the exit code is 1, and a full
# report is written to tests/report.txt regardless of outcome.
#
# If a run is interrupted (Ctrl-C, a crash, or a hang) rather than failing
# cleanly, the container is left running the same way, and the next run
# will refuse to start until you remove it by hand:
#   docker rm -f -v sillysite-test
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TESTS_DIR/.." && pwd)"
REPORT_FILE="$TESTS_DIR/report.txt"

# shellcheck source=lib/framework.sh
source "$TESTS_DIR/lib/framework.sh"
# shellcheck source=lib/docker.sh
source "$TESTS_DIR/lib/docker.sh"
# shellcheck source=lib/api.sh
source "$TESTS_DIR/lib/api.sh"
# shellcheck source=lib/proc.sh
source "$TESTS_DIR/lib/proc.sh"

preflight_checks
check_no_leftover_container

TEST_PORT="$(find_free_port 19700)"
ADMIN_KEY="testsuitekey0000000000000000000000000000"
BASE_URL="http://127.0.0.1:${TEST_PORT}"

build_image
start_container
wait_for_healthy

for case_file in "$TESTS_DIR"/cases/*.sh; do
    # shellcheck source=/dev/null
    source "$case_file"
done

echo
echo "Running ${#TEST_FN[@]} tests against $BASE_URL ..."
echo

run_all_tests

echo
echo "Passed: $PASS_COUNT / ${#TEST_FN[@]}"
echo "Failed: $FAIL_COUNT / ${#TEST_FN[@]}"
echo "Full report: $REPORT_FILE"

if [ "$FAIL_COUNT" -eq 0 ]; then
    cleanup_docker
    exit 0
else
    print_postmortem_info
    exit 1
fi
