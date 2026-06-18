#!/usr/bin/env bash
# Stop-hook entry point: runs tests/fast_check.sh only if any watched app
# file changed since the last check (tracked via a content hash in
# tests/.fast_check_hash), and reports failures via a systemMessage.
# Silent -- no output at all -- when nothing changed or everything passes,
# so it doesn't add noise to ordinary turns.
#
# Always exits 0: this is meant to flag failures, not block the turn from
# ending or otherwise interfere with the session.
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TESTS_DIR/.." && pwd)"
HASH_FILE="$TESTS_DIR/.fast_check_hash"

WATCHED_FILES=(main.py business.py auth.py config.py database.py models.py schemas.py)

cd "$PROJECT_ROOT" || exit 0

current_hash="$(sha256sum "${WATCHED_FILES[@]}" 2>/dev/null | sha256sum | cut -d' ' -f1)"
[ -n "$current_hash" ] || exit 0

previous_hash=""
[ -f "$HASH_FILE" ] && previous_hash="$(cat "$HASH_FILE")"

if [ "$current_hash" = "$previous_hash" ]; then
    exit 0
fi

output="$("$TESTS_DIR/fast_check.sh" 2>&1)"
rc=$?

# Recorded after running (not before), so a crash mid-run is retried on
# the next turn instead of being silently considered "checked".
echo "$current_hash" > "$HASH_FILE"

if [ "$rc" -ne 0 ]; then
    summary="$(printf '%s\n' "$output" | grep -E '^(Passed|Failed):' | tr '\n' ' ')"
    python3 -c "
import json, sys
msg = 'Fast test check found failures after app-code changes this turn. ' + sys.argv[1] + '(See tests/fast_report.txt for details, or tests/run_tests.sh for the full suite.)'
print(json.dumps({'systemMessage': msg}))
" "$summary"
fi

exit 0
