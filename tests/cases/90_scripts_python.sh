# Python CLI utility scripts (login.py, changepw.py).

test_script_login_success() {
    local user pw token
    user="$(unique_name scriptloginok)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    token="$(printf '%s\n' "$pw" | "$PROJECT_ROOT/login.py" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_script_login_success "login.py succeeds and prints a token" \
    "./login.py <url> <username> with the correct password (piped via getpass) exits 0 and prints a 64-char hex token"

test_script_login_wrong_password() {
    local user pw
    user="$(unique_name scriptloginwrong)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\n' "not-$pw" | "$PROJECT_ROOT/login.py" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "login.py unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "Login failed"
}
register_test test_script_login_wrong_password "login.py fails on wrong password" \
    "./login.py with an incorrect password exits non-zero and prints \"Login failed: ...\" to stderr"

test_script_changepw_success() {
    local user pw newpw
    user="$(unique_name scriptchangepwok)"
    pw="pw_${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }

    local out
    out="$(printf '%s\n%s\n%s\n' "$pw" "$newpw" "$newpw" | "$PROJECT_ROOT/changepw.py" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    assert_contains "$out" "Password changed successfully" || return 1

    login_as "$user" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_script_changepw_success "changepw.py changes the password" \
    "./changepw.py with matching new-password confirmation exits 0, and the new password then works"

test_script_changepw_mismatch() {
    local user pw
    user="$(unique_name scriptchangepwmismatch)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\nnewpw1\nnewpw2\n' "$pw" | "$PROJECT_ROOT/changepw.py" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "changepw.py unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "do not match"
}
register_test test_script_changepw_mismatch "changepw.py rejects mismatched confirmation" \
    "./changepw.py exits non-zero with \"passwords do not match\" if the new password and confirmation differ"
