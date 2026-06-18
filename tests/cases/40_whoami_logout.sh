# /whoami and /logout.

test_whoami_no_auth() {
    api GET /whoami
    assert_eq 401 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Invalid or missing API key"
}
register_test test_whoami_no_auth "whoami without auth is rejected" \
    "GET /whoami with no apikey fails with 401 \"Invalid or missing API key\""

test_whoami_with_session() {
    new_logged_in_user whoamisession || { echo "setup failed"; return 1; }
    api GET /whoami "$TOKEN"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "\"username\":\"$TEST_USERNAME\"" "username" || return 1
    local login_at session_expires_at
    login_at="$(json_get "$BODY" "['login_at']")"
    session_expires_at="$(json_get "$BODY" "['session_expires_at']")"
    [ -n "$login_at" ] && [ "$login_at" != "None" ] || { echo "expected non-null login_at"; return 1; }
    [ -n "$session_expires_at" ] && [ "$session_expires_at" != "None" ] || { echo "expected non-null session_expires_at"; return 1; }
}
register_test test_whoami_with_session "whoami with a session shows login info" \
    "GET /whoami with a session token returns the username plus non-null login_at/session_expires_at"

test_whoami_with_static_key() {
    api GET /whoami "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"username":"admin"' "username" || return 1
    local login_at
    login_at="$(json_get "$BODY" "['login_at']")"
    [ "$login_at" = "None" ] || { echo "expected null login_at for static key, got: $login_at"; return 1; }
}
register_test test_whoami_with_static_key "whoami with static key has no session info" \
    "GET /whoami authenticated with the static API key shows username \"admin\" with null login_at/session_expires_at (no associated session)"

test_logout_with_session() {
    new_logged_in_user logoutsession || { echo "setup failed"; return 1; }
    api GET /logout "$TOKEN"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "logged out"
}
register_test test_logout_with_session "logout invalidates the session" \
    "GET /logout with a session token returns 200 with a confirmation message"

test_logout_static_key_rejected() {
    api GET /logout "$ADMIN_KEY"
    assert_eq 400 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Cannot log out the static API key"
}
register_test test_logout_static_key_rejected "logout rejects the static API key" \
    "GET /logout authenticated with the static API key fails with 400, since it has no session to invalidate"

test_token_unusable_after_logout() {
    new_logged_in_user afterlogout || { echo "setup failed"; return 1; }
    api GET /logout "$TOKEN"
    [ "$STATUS" = "200" ] || { echo "logout failed: $STATUS"; return 1; }
    api GET /whoami "$TOKEN"
    assert_eq 401 "$STATUS" "status reusing token after logout"
}
register_test test_token_unusable_after_logout "token is dead after logout" \
    "Using a session token again after /logout fails with 401"

test_double_logout() {
    new_logged_in_user doublelogout || { echo "setup failed"; return 1; }
    api GET /logout "$TOKEN"
    [ "$STATUS" = "200" ] || { echo "first logout failed: $STATUS"; return 1; }
    api GET /logout "$TOKEN"
    assert_eq 401 "$STATUS" "status on second logout"
}
register_test test_double_logout "logging out twice fails the second time" \
    "Calling /logout again with an already-invalidated token fails with 401, not a duplicate success"
