# JavaScript client library and Node CLI scripts (js/).

test_js_login_success() {
    local user pw token
    user="$(unique_name jsloginok)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    local out
    out="$(printf '%s\n' "$pw" | node "$PROJECT_ROOT/js/login.js" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_js_login_success "login.js succeeds and prints a token" \
    "node js/login.js with the correct password (piped via stdin) exits 0 and prints a 64-char hex token"

test_js_login_wrong_password() {
    local user pw
    user="$(unique_name jsloginwrong)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\n' "wrong-$pw" | node "$PROJECT_ROOT/js/login.js" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "login.js unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "Login failed"
}
register_test test_js_login_wrong_password "login.js fails on wrong password" \
    "node js/login.js with an incorrect password exits non-zero and prints \"Login failed: ...\" to stderr"

test_js_logout_success() {
    new_logged_in_user jslogout || { echo "setup failed"; return 1; }
    local out
    out="$(node "$PROJECT_ROOT/js/logout.js" "$BASE_URL" "$TOKEN" 2>&1)"
    local rc=$?
    [ "$rc" -eq 0 ] || { echo "$out"; return 1; }
    assert_contains "$out" "logged out"
}
register_test test_js_logout_success "logout.js invalidates the session" \
    "node js/logout.js exits 0 and prints the server's logout confirmation message"

test_js_changepw_success() {
    local user pw newpw out
    user="$(unique_name jschangepwok)"
    pw="pw_${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(printf '%s\n%s\n%s\n' "$pw" "$newpw" "$newpw" | node "$PROJECT_ROOT/js/changepw.js" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    assert_contains "$out" "Password changed successfully" || return 1
    login_as "$user" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_js_changepw_success "changepw.js changes the password" \
    "node js/changepw.js with matching new-password confirmation exits 0, and the new password then works"

test_js_changepw_mismatch() {
    local user pw
    user="$(unique_name jschangepwmismatch)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\nnewpw1\nnewpw2\n' "$pw" | node "$PROJECT_ROOT/js/changepw.js" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "changepw.js unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "do not match"
}
register_test test_js_changepw_mismatch "changepw.js rejects mismatched confirmation" \
    "node js/changepw.js exits non-zero with \"passwords do not match\" if the new password and confirmation differ"
