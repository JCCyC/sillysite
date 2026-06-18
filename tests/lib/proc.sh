# Helpers for driving external client programs (C binaries, Node scripts)
# and inspecting their output.

# pty_drive <timeout_seconds> [<prompt> <answer>]... -- <command> [args...]
# See tests/lib/pty_drive.py for details. Needed for the C client, which
# reads passwords from /dev/tty rather than stdin.
pty_drive() {
    python3 "$TESTS_DIR/lib/pty_drive.py" "$@"
}

# last_nonblank_line <text>
# Strips \r (pty output is in cooked mode and translates \n to \r\n) before
# picking the last non-blank line, so length checks on the result are exact.
last_nonblank_line() {
    printf '%s\n' "$1" | tr -d '\r' | grep -v '^[[:space:]]*$' | tail -n1
}
