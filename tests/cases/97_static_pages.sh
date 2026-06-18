# static/*.html pages, driven via a real headless Chrome over the
# WebDriver protocol. This is the only place the *browser* code path of
# js/sillysite.js (fetch + crypto.subtle, as opposed to the Node code path
# already covered by the js/ binding tests) gets exercised end to end.

test_static_pages_full_flow() {
    command -v chromedriver > /dev/null 2>&1 || { echo "chromedriver not installed, skipping"; return 1; }

    local user pw newpw
    user="$(unique_name staticpages)"
    pw="pw_${RANDOM}${RANDOM}"
    newpw="new_${RANDOM}${RANDOM}"
    create_user "$user" "$pw" || { echo "setup failed"; return 1; }

    python3 "$TESTS_DIR/lib/browser_e2e.py" "$BASE_URL" "$user" "$pw" "$newpw"
}
register_test test_static_pages_full_flow "static pages: login, whoami, changepw" \
    "Drives a real headless Chrome through login.html -> whoami.html -> changepw.html -> re-login, exercising the actual crypto.subtle/fetch code shared via /sillysite.js"
