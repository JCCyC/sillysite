# C client library and CLI programs (c/).

test_c_build() {
    (cd "$PROJECT_ROOT/c" && make clean > /dev/null 2>&1 && make)
}
register_test test_c_build "C client builds cleanly via make" \
    "make clean && make in c/ succeeds, producing libsillysite.a, login, and changepw"

test_c_login_success() {
    [ -x "$PROJECT_ROOT/c/login" ] || { echo "c/login missing, did the build fail?"; return 1; }
    local user pw out token
    user="$(unique_name cloginok)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(pty_drive 10 "Password: " "$pw" -- "$PROJECT_ROOT/c/login" "$BASE_URL" "$user")"
    local rc=$?
    [ "$rc" -eq 0 ] || { echo "$out"; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_c_login_success "c/login succeeds and prints a token" \
    "The C login program, driven over a pty, exits 0 and prints a 64-char hex token"

test_c_login_wrong_password() {
    [ -x "$PROJECT_ROOT/c/login" ] || { echo "c/login missing, did the build fail?"; return 1; }
    local user pw out
    user="$(unique_name cloginwrong)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(pty_drive 10 "Password: " "wrong-$pw" -- "$PROJECT_ROOT/c/login" "$BASE_URL" "$user")"
    local rc=$?
    [ "$rc" -ne 0 ] || { echo "c/login unexpectedly succeeded: $out"; return 1; }
    # The C library maps HTTP status to errno (403 -> EACCES) and the CLI
    # prints strerror(errno), not the server's literal detail text -- see
    # c/README-C.md's errno table.
    assert_contains "$(last_nonblank_line "$out")" "Permission denied"
}
register_test test_c_login_wrong_password "c/login fails on wrong password" \
    "The C login program exits non-zero and reports strerror(EACCES) (\"Permission denied\") for a wrong password, per its errno-based design"

test_c_changepw_success() {
    [ -x "$PROJECT_ROOT/c/changepw" ] || { echo "c/changepw missing, did the build fail?"; return 1; }
    local user pw newpw out
    user="$(unique_name cchangepwok)"
    pw="pw_${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(pty_drive 10 "Current password: " "$pw" "New password: " "$newpw" "Confirm new password: " "$newpw" -- "$PROJECT_ROOT/c/changepw" "$BASE_URL" "$user")"
    local rc=$?
    [ "$rc" -eq 0 ] || { echo "$out"; return 1; }
    assert_contains "$(last_nonblank_line "$out")" "Password changed successfully" || return 1
    login_as "$user" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_c_changepw_success "c/changepw changes the password" \
    "The C changepw program, driven over a pty through all three prompts, exits 0 and the new password then works"
