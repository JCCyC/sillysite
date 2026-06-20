# C# client library and CLI programs (csharp/), built against Mono.

test_csharp_build() {
    (cd "$PROJECT_ROOT/csharp" && make clean > /dev/null 2>&1 && make)
}
register_test test_csharp_build "C# client builds cleanly via make" \
    "make clean && make in csharp/ succeeds, producing Sillysite.dll, Login.exe, and ChangePw.exe"

test_csharp_login_success() {
    [ -x "$PROJECT_ROOT/csharp/login" ] || { echo "csharp/login missing, did the build fail?"; return 1; }
    local user pw token
    user="$(unique_name csloginok)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    local out
    out="$(printf '%s\n' "$pw" | "$PROJECT_ROOT/csharp/login" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_csharp_login_success "csharp/login succeeds and prints a token" \
    "csharp/login with the correct password (piped via stdin) exits 0 and prints a 64-char hex token"

test_csharp_login_wrong_password() {
    [ -x "$PROJECT_ROOT/csharp/login" ] || { echo "csharp/login missing, did the build fail?"; return 1; }
    local user pw
    user="$(unique_name csloginwrong)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\n' "wrong-$pw" | "$PROJECT_ROOT/csharp/login" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "csharp/login unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "Login failed"
}
register_test test_csharp_login_wrong_password "csharp/login fails on wrong password" \
    "csharp/login with an incorrect password exits non-zero and prints \"Login failed: ...\" to stderr"

test_csharp_changepw_success() {
    [ -x "$PROJECT_ROOT/csharp/changepw" ] || { echo "csharp/changepw missing, did the build fail?"; return 1; }
    local user pw newpw out
    user="$(unique_name cschangepwok)"
    pw="pw_${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    out="$(printf '%s\n%s\n%s\n' "$pw" "$newpw" "$newpw" | "$PROJECT_ROOT/csharp/changepw" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    assert_contains "$out" "Password changed successfully" || return 1
    login_as "$user" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_csharp_changepw_success "csharp/changepw changes the password" \
    "csharp/changepw with matching new-password confirmation exits 0, and the new password then works"

test_csharp_changepw_mismatch() {
    [ -x "$PROJECT_ROOT/csharp/changepw" ] || { echo "csharp/changepw missing, did the build fail?"; return 1; }
    local user pw
    user="$(unique_name cschangepwmismatch)"
    pw="pw_${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    if printf '%s\nnewpw1\nnewpw2\n' "$pw" | "$PROJECT_ROOT/csharp/changepw" "$BASE_URL" "$user" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "csharp/changepw unexpectedly succeeded"
        return 1
    fi
    assert_contains "$(cat /tmp/sillysite_test_err)" "do not match"
}
register_test test_csharp_changepw_mismatch "csharp/changepw rejects mismatched confirmation" \
    "csharp/changepw exits non-zero with \"passwords do not match\" if the new password and confirmation differ"

test_csharp_login_non_ascii_password() {
    [ -x "$PROJECT_ROOT/csharp/login" ] || { echo "csharp/login missing, did the build fail?"; return 1; }
    local user pw token
    user="$(unique_name csnonascii)"
    pw=$'pâsswörd£€日本語_'"${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }
    local out
    out="$(printf '%s\n' "$pw" | "$PROJECT_ROOT/csharp/login" "$BASE_URL" "$user" 2>/tmp/sillysite_test_err)"
    local rc=$?
    [ "$rc" -eq 0 ] || { cat /tmp/sillysite_test_err; return 1; }
    token="$(last_nonblank_line "$out")"
    [ "${#token}" -eq 64 ] || { echo "unexpected token: $token"; return 1; }
}
register_test test_csharp_login_non_ascii_password "csharp/login works with a non-ASCII password" \
    "csharp/login derives PBKDF2 over the password's UTF-8 bytes, matching the server's Python-side hashing, for a password with accented/currency/CJK characters"
