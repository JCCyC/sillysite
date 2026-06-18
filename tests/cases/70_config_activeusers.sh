# /config and /activeusers (both admin-only).

test_config_admin() {
    api GET /config "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "session_ttl_seconds"
}
register_test test_config_admin "admin can read app config" \
    "GET /config as admin returns 200 with the app_config key/value settings"

test_config_non_admin() {
    new_logged_in_user confignonadmin || { echo "setup failed"; return 1; }
    api GET /config "$TOKEN"
    assert_eq 403 "$STATUS" "status"
}
register_test test_config_non_admin "reading config requires admin" \
    "GET /config as a non-admin fails with 403"

test_config_no_auth() {
    api GET /config
    assert_eq 401 "$STATUS" "status"
}
register_test test_config_no_auth "reading config requires auth" \
    "GET /config with no apikey fails with 401"

test_activeusers_admin() {
    new_logged_in_user activeuserscheck || { echo "setup failed"; return 1; }
    api GET /activeusers "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "\"username\":\"$TEST_USERNAME\"" || return 1
    # Find the matching entry's source_ip without assuming a fixed value:
    # requests arrive via Docker's NAT'd bridge gateway, not 127.0.0.1.
    local source_ip
    source_ip="$(python3 -c "
import json, sys
entries = json.loads(sys.argv[1])
for e in entries:
    if e['username'] == sys.argv[2]:
        print(e['source_ip'])
        break
" "$BODY" "$TEST_USERNAME")"
    [ -n "$source_ip" ] || { echo "no source_ip found for $TEST_USERNAME"; return 1; }
}
register_test test_activeusers_admin "admin sees active sessions" \
    "GET /activeusers as admin lists the just-logged-in test user with their source IP"

test_activeusers_non_admin() {
    new_logged_in_user activeusersnonadmin || { echo "setup failed"; return 1; }
    api GET /activeusers "$TOKEN"
    assert_eq 403 "$STATUS" "status"
}
register_test test_activeusers_non_admin "listing active users requires admin" \
    "GET /activeusers as a non-admin fails with 403"
