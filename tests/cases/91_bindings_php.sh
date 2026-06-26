# PHP client library and CLI scripts (php/).

test_php_lints_cleanly() {
    for f in "$PROJECT_ROOT"/php/*.php; do
        php -l "$f" > /dev/null || return 1
    done
}
register_test test_php_lints_cleanly "PHP client lints cleanly" \
    "php -l on every php/*.php file succeeds -- PHP has no build step, so this is the rough equivalent of the C/Java/C# build checks"

test_php_login_success() {
    local user pw token
    user="$(unique_name phploginok)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    local out
    out="$(printf '%s\n' "$pw" | php "$PROJECT_ROOT/php/login.php" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_php_login_success "php/login.php succeeds and prints a token" \
    "php/login.php with the correct password (piped via stdin) exits 0 and prints a 64-char hex token"

test_php_login_wrong_password() {
    local user pw
    user="$(unique_name phploginwrong)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\n' "wrong-$pw" | php "$PROJECT_ROOT/php/login.php" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "php/login.php unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "Login failed"
}
register_test test_php_login_wrong_password "php/login.php fails on wrong password" \
    "php/login.php with an incorrect password exits non-zero and prints \"Login failed: ...\" to stderr"

test_php_changepw_success() {
    local user pw newpw out
    user="$(unique_name phpchangepwok)"
    pw="pw_${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(printf '%s\n%s\n%s\n' "$pw" "$newpw" "$newpw" | php "$PROJECT_ROOT/php/changepw.php" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    assert_contains "$out" "Password changed successfully" || return 1
    login_as "$user" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_php_changepw_success "php/changepw.php changes the password" \
    "php/changepw.php with matching new-password confirmation exits 0, and the new password then works"

test_php_changepw_mismatch() {
    local user pw
    user="$(unique_name phpchangepwmismatch)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\nnewpw1\nnewpw2\n' "$pw" | php "$PROJECT_ROOT/php/changepw.php" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "php/changepw.php unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "do not match"
}
register_test test_php_changepw_mismatch "php/changepw.php rejects mismatched confirmation" \
    "php/changepw.php exits non-zero with \"passwords do not match\" if the new password and confirmation differ"

test_php_login_non_ascii_password() {
    local user pw token
    user="$(unique_name phpnonascii)"
    pw=$'pâsswörd£€日本語_'"${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    local out
    out="$(printf '%s\n' "$pw" | php "$PROJECT_ROOT/php/login.php" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_php_login_non_ascii_password "php/login.php works with a non-ASCII password" \
    "php/login.php derives PBKDF2 over the password's UTF-8 bytes, matching the server's Python-side hashing, for a password with accented/currency/CJK characters"
