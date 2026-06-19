# Public, unauthenticated endpoints.

test_root_redirect_no_key() {
    local code location
    code="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/")"
    location="$(curl -s -o /dev/null -w '%{redirect_url}' "$BASE_URL/")"
    assert_eq 307 "$code" "status" || return 1
    assert_contains "$location" "/login.html" "location"
}
register_test test_root_redirect_no_key "GET / redirects to /login.html" \
    "GET / with no apikey should 307 redirect to /login.html"

test_root_redirect_with_key() {
    local location
    location="$(curl -s -o /dev/null -w '%{redirect_url}' -H "X-API-Key: $ADMIN_KEY" "$BASE_URL/")"
    assert_contains "$location" "/login.html?apikey=$ADMIN_KEY" "location"
}
register_test test_root_redirect_with_key "GET / with apikey carries it along" \
    "GET / with a valid X-API-Key should 307 redirect to /login.html?apikey=<that key>"

test_about_public() {
    api GET /about
    assert_eq 200 "$STATUS" "status" || return 1
    local msg
    msg="$(json_get "$BODY" "['msg']")"
    [ -n "$msg" ] || { echo "empty msg field"; return 1; }
}
register_test test_about_public "GET /about returns a random message" \
    "GET /about requires no auth and returns {\"msg\": \"<random message>\"}"

test_favicon() {
    api GET /favicon.ico
    assert_eq 200 "$STATUS" "status"
}
register_test test_favicon "GET /favicon.ico serves the icon" \
    "GET /favicon.ico requires no auth and returns 200"

test_login_html_no_key() {
    api GET /login.html
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "SillySite" "body"
}
register_test test_login_html_no_key "GET /login.html serves the login form" \
    "GET /login.html with no apikey serves static/login.html (200)"

test_login_html_with_valid_key() {
    new_logged_in_user lhtmlvalid || { echo "setup failed"; return 1; }
    local location
    location="$(curl -s -o /dev/null -w '%{redirect_url}' -H "X-API-Key: $TOKEN" "$BASE_URL/login.html")"
    assert_contains "$location" "/whoami.html?apikey=$TOKEN" "location"
}
register_test test_login_html_with_valid_key "GET /login.html skips form if logged in" \
    "GET /login.html with a valid apikey redirects (307) to /whoami.html?apikey=<key> instead of serving the form"

test_login_html_with_invalid_key() {
    api GET /login.html "bogus-not-a-real-key"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "SillySite" "body"
}
register_test test_login_html_with_invalid_key "GET /login.html ignores bad apikey" \
    "GET /login.html with an invalid/expired apikey still serves the login form (200), not an error"

test_whoami_html_no_key() {
    local location
    location="$(curl -s -o /dev/null -w '%{redirect_url}' "$BASE_URL/whoami.html")"
    assert_contains "$location" "/login.html" "location"
}
register_test test_whoami_html_no_key "GET /whoami.html redirects when logged out" \
    "GET /whoami.html with no valid apikey redirects to /login.html"

test_changepw_html_no_key() {
    local location
    location="$(curl -s -o /dev/null -w '%{redirect_url}' "$BASE_URL/changepw.html")"
    assert_contains "$location" "/login.html" "location"
}
register_test test_changepw_html_no_key "GET /changepw.html redirects when logged out" \
    "GET /changepw.html with no valid apikey redirects to /login.html"

test_apikey_via_query_param() {
    api GET "/whoami?apikey=$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"username":"admin"' "body"
}
register_test test_apikey_via_query_param "apikey query param works like header" \
    "GET /whoami?apikey=<key> (no header) authenticates the same as the X-API-Key header"

test_apikey_both_header_and_query_rejected() {
    local code
    code="$(curl -s -o /tmp/sillysite_test_body -w '%{http_code}' -H "X-API-Key: $ADMIN_KEY" "$BASE_URL/whoami?apikey=$ADMIN_KEY")"
    assert_eq 401 "$code" "status"
}
register_test test_apikey_both_header_and_query_rejected "header+query apikey together is rejected" \
    "Providing X-API-Key header AND apikey query param simultaneously is treated as unauthenticated (401), even if they match"
