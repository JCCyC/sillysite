# HTTP and JSON helpers shared by API test cases. Requires $BASE_URL and
# $ADMIN_KEY to be set (done by run_tests.sh after the container is up).

# api <method> <path> [apikey] [json-body]
# Sets $STATUS (HTTP status code, or 000 on transport error) and $BODY.
api() {
    local method="$1" path="$2" apikey="${3:-}" body="${4:-}"
    local args=(-s -o /tmp/sillysite_test_body -w '%{http_code}' -X "$method")
    [ -n "$apikey" ] && args+=(-H "X-API-Key: $apikey")
    [ -n "$body" ] && args+=(-H "Content-Type: application/json" -d "$body")
    STATUS="$(curl "${args[@]}" "$BASE_URL$path")"
    BODY="$(cat /tmp/sillysite_test_body 2>/dev/null)"
}

# json_get <json> <python-subscript-expr, e.g. "['token']" or "[0]['name']">
json_get() {
    python3 -c "
import json, sys
d = json.loads(sys.argv[1])
print(d$2)
" "$1" "$2" 2>/dev/null
}

# unique_name <prefix> -- short, collision-resistant username/token for this run
unique_name() {
    echo "$1_$$_${RANDOM}${RANDOM}"
}

# create_user <username> <password> [full_name] [is_admin: true|false]
# Creates the user as admin (via the static API key). Returns 1 on failure.
create_user() {
    local username="$1" password="$2" full_name="${3:-Test User}" is_admin="${4:-false}"
    api POST /users "$ADMIN_KEY" "{\"username\":\"$username\",\"full_name\":\"$full_name\",\"password\":\"$password\",\"is_admin\":$is_admin}"
    [ "$STATUS" = "201" ]
}

# login_as <username> <password>
# Uses the project's own login.py to obtain a session token into $TOKEN.
# Returns 1 (with $TOKEN unset) on failure.
login_as() {
    local username="$1" password="$2"
    TOKEN="$(printf '%s\n' "$password" | detached "$PROJECT_ROOT/login.py" "$BASE_URL" "$username" 2>/tmp/sillysite_test_err)"
    local rc=$?
    if [ "$rc" -ne 0 ] || [ -z "$TOKEN" ]; then
        cat /tmp/sillysite_test_err >&2
        unset TOKEN
        return 1
    fi
    return 0
}

# new_password_creds <password>
# Prints "<salt_hex> <hash_hex> <iterations>" for use as new_salt/
# new_password_hash/new_iterations in a raw POST /change-password call.
new_password_creds() {
    python3 -c "
import hashlib, os, sys
password = sys.argv[1]
salt = os.urandom(16)
iterations = 200000
h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations, dklen=32)
print(salt.hex(), h.hex(), iterations)
" "$1"
}

# new_logged_in_user <prefix> [is_admin]
# Creates a fresh user with a random password, logs in, and sets
# $TEST_USERNAME, $TEST_PASSWORD, and $TOKEN. Returns 1 on any failure.
new_logged_in_user() {
    local prefix="$1" is_admin="${2:-false}"
    TEST_USERNAME="$(unique_name "$prefix")"
    TEST_PASSWORD="pw_${RANDOM}${RANDOM}"
    create_user "$TEST_USERNAME" "$TEST_PASSWORD" "Test User" "$is_admin" || return 1
    login_as "$TEST_USERNAME" "$TEST_PASSWORD" || return 1
}
