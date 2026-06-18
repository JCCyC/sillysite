# /change-password flow, at the raw API level.

test_change_password_success() {
    new_logged_in_user changepwok || { echo "setup failed"; return 1; }
    local newpw="new_${RANDOM}${RANDOM}"
    local creds salt hash iterations
    creds="$(new_password_creds "$newpw")"
    salt="$(echo "$creds" | cut -d' ' -f1)"
    hash="$(echo "$creds" | cut -d' ' -f2)"
    iterations="$(echo "$creds" | cut -d' ' -f3)"

    api POST /change-password "$TOKEN" "{\"new_salt\":\"$salt\",\"new_password_hash\":\"$hash\",\"new_iterations\":$iterations}"
    assert_eq 204 "$STATUS" "status" || return 1
    [ -z "$BODY" ] || { echo "expected empty body, got: $BODY"; return 1; }

    login_as "$TEST_USERNAME" "$newpw" || { echo "login with new password failed"; return 1; }
}
register_test test_change_password_success "change-password succeeds with 204" \
    "POST /change-password with a session token returns 204 with an empty body, and the new password works for a subsequent login"

test_change_password_old_password_rejected() {
    new_logged_in_user changepwold || { echo "setup failed"; return 1; }
    local oldpw="$TEST_PASSWORD"
    local newpw="new_${RANDOM}${RANDOM}"
    local creds salt hash iterations
    creds="$(new_password_creds "$newpw")"
    salt="$(echo "$creds" | cut -d' ' -f1)"
    hash="$(echo "$creds" | cut -d' ' -f2)"
    iterations="$(echo "$creds" | cut -d' ' -f3)"
    api POST /change-password "$TOKEN" "{\"new_salt\":\"$salt\",\"new_password_hash\":\"$hash\",\"new_iterations\":$iterations}"
    [ "$STATUS" = "204" ] || { echo "change-password setup failed: $STATUS"; return 1; }

    if printf '%s\n' "$oldpw" | detached "$PROJECT_ROOT/login.py" "$BASE_URL" "$TEST_USERNAME" >/dev/null 2>/tmp/sillysite_test_err; then
        echo "login with old password unexpectedly succeeded"
        return 1
    fi
}
register_test test_change_password_old_password_rejected "old password stops working" \
    "After a successful change-password, logging in with the old password fails"

test_change_password_session_single_use() {
    new_logged_in_user changepwsingleuse || { echo "setup failed"; return 1; }
    local newpw="new_${RANDOM}${RANDOM}"
    local creds salt hash iterations
    creds="$(new_password_creds "$newpw")"
    salt="$(echo "$creds" | cut -d' ' -f1)"
    hash="$(echo "$creds" | cut -d' ' -f2)"
    iterations="$(echo "$creds" | cut -d' ' -f3)"
    api POST /change-password "$TOKEN" "{\"new_salt\":\"$salt\",\"new_password_hash\":\"$hash\",\"new_iterations\":$iterations}"
    [ "$STATUS" = "204" ] || { echo "change-password setup failed: $STATUS"; return 1; }

    api GET /whoami "$TOKEN"
    assert_eq 401 "$STATUS" "status reusing the change-password session token"
}
register_test test_change_password_session_single_use "change-password session can't be reused" \
    "The session token used to authorize a password change is expired immediately afterward, even on success"

test_change_password_timeout() {
    local orig rc=0
    orig="$(db_get_config change_pw_timeout_seconds)"
    db_set_config change_pw_timeout_seconds 1

    if ! new_logged_in_user changepwtimeout; then
        echo "setup failed"
        rc=1
    fi

    if [ "$rc" -eq 0 ]; then
        sleep 2
        local creds salt hash iterations
        creds="$(new_password_creds "irrelevant")"
        salt="$(echo "$creds" | cut -d' ' -f1)"
        hash="$(echo "$creds" | cut -d' ' -f2)"
        iterations="$(echo "$creds" | cut -d' ' -f3)"
        api POST /change-password "$TOKEN" "{\"new_salt\":\"$salt\",\"new_password_hash\":\"$hash\",\"new_iterations\":$iterations}"
        if [ "$STATUS" != "403" ]; then
            echo "expected 403, got $STATUS"
            rc=1
        elif ! assert_contains "$BODY" "Change password timeout"; then
            rc=1
        fi
    fi

    db_set_config change_pw_timeout_seconds "$orig"
    return "$rc"
}
register_test test_change_password_timeout "change-password after timeout is rejected" \
    "If change_pw_timeout_seconds elapses after login, /change-password fails with 403 \"Change password timeout\""

test_change_password_static_key_no_timeout() {
    local newpw="adminTestPw_${RANDOM}${RANDOM}"
    local creds salt hash iterations
    creds="$(new_password_creds "$newpw")"
    salt="$(echo "$creds" | cut -d' ' -f1)"
    hash="$(echo "$creds" | cut -d' ' -f2)"
    iterations="$(echo "$creds" | cut -d' ' -f3)"
    api POST /change-password "$ADMIN_KEY" "{\"new_salt\":\"$salt\",\"new_password_hash\":\"$hash\",\"new_iterations\":$iterations}"
    assert_eq 204 "$STATUS" "status" || return 1

    login_as admin "$newpw" || { echo "login as admin with new password failed"; return 1; }
}
register_test test_change_password_static_key_no_timeout "static key change-password isn't timed" \
    "POST /change-password authenticated with the static API key (no session) succeeds and isn't subject to the change-password timeout"
