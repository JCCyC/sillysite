# /users CRUD and access control (admin-only).

test_users_list_no_auth() {
    api GET /users
    assert_eq 401 "$STATUS" "status"
}
register_test test_users_list_no_auth "listing users requires auth" \
    "GET /users with no apikey fails with 401"

test_users_list_non_admin() {
    new_logged_in_user userslistnonadmin || { echo "setup failed"; return 1; }
    api GET /users "$TOKEN"
    assert_eq 403 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Admin privileges required"
}
register_test test_users_list_non_admin "listing users requires admin" \
    "GET /users as a non-admin fails with 403 \"Admin privileges required\""

test_users_list_admin() {
    api GET /users "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"username":"admin"'
}
register_test test_users_list_admin "admin can list users" \
    "GET /users as admin returns 200 with a list including the admin user"

test_users_create_as_admin() {
    local user="$(unique_name userscreate)"
    api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"Create Test\",\"password\":\"pw_${RANDOM}\"}"
    assert_eq 201 "$STATUS" "status" || return 1
    assert_contains "$BODY" "\"username\":\"$user\"" || return 1
    assert_not_contains "$BODY" "password"
}
register_test test_users_create_as_admin "admin can create a user" \
    "POST /users as admin returns 201 with the new user (and never echoes back password fields)"

test_users_create_no_email_defaults_null() {
    local user="$(unique_name userscreatenoemail)"
    api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"No Email\",\"password\":\"pw_${RANDOM}\"}"
    assert_eq 201 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"email":null'
}
register_test test_users_create_no_email_defaults_null "creating a user without an email leaves it null" \
    "POST /users with no email field succeeds and the response shows \"email\":null -- email is optional"

test_users_create_with_email() {
    local user="$(unique_name userscreateemail)"
    api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"Has Email\",\"email\":\"$user@example.com\",\"password\":\"pw_${RANDOM}\"}"
    assert_eq 201 "$STATUS" "status" || return 1
    assert_contains "$BODY" "\"email\":\"$user@example.com\""
}
register_test test_users_create_with_email "admin can create a user with a well-formed email" \
    "POST /users with a valid email succeeds with 201 and echoes the email back"

test_users_create_with_malformed_email() {
    local user="$(unique_name usersbademail)"
    api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"Bad Email\",\"email\":\"not-an-email\",\"password\":\"pw_${RANDOM}\"}"
    assert_eq 422 "$STATUS" "status"
}
register_test test_users_create_with_malformed_email "creating a user rejects a malformed email" \
    "POST /users with a syntactically invalid email fails with 422, no user is created"

test_users_create_rejects_various_malformed_emails() {
    local bad_emails=(
        "notanemail"
        "a@b@example.com"
        "a@b@c@example.com"
        "@example.com"
        "user@"
        "user@@example.com"
        "user name@example.com"
    )
    local email user
    for email in "${bad_emails[@]}"; do
        user="$(unique_name usersbademail2)"
        api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"Bad Email\",\"email\":\"$email\",\"password\":\"pw_${RANDOM}\"}"
        if [ "$STATUS" != "422" ]; then
            echo "email '$email' expected 422, got $STATUS: $BODY"
            return 1
        fi
    done
}
register_test test_users_create_rejects_various_malformed_emails "creating a user rejects malformed email shapes" \
    "POST /users fails with 422 for emails with no @, more than two @, a missing local or domain part, or an embedded space"

test_admin_default_email_is_null() {
    api GET /whoami "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"email":null'
}
register_test test_admin_default_email_is_null "the default admin user has no email" \
    "GET /whoami as the static admin key shows \"email\":null for the non-removable default admin profile"

test_users_create_duplicate() {
    local user="$(unique_name usersdup)"
    create_user "$user" "pw_${RANDOM}" || { echo "first create failed"; return 1; }
    api POST /users "$ADMIN_KEY" "{\"username\":\"$user\",\"full_name\":\"Dup\",\"password\":\"pw2_${RANDOM}\"}"
    assert_eq 409 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Username already exists"
}
register_test test_users_create_duplicate "duplicate username is rejected" \
    "POST /users with an already-taken username fails with 409"

test_users_create_non_admin() {
    new_logged_in_user userscreatenonadmin || { echo "setup failed"; return 1; }
    api POST /users "$TOKEN" "{\"username\":\"$(unique_name shouldnotexist)\",\"full_name\":\"X\",\"password\":\"pw\"}"
    assert_eq 403 "$STATUS" "status"
}
register_test test_users_create_non_admin "creating a user requires admin" \
    "POST /users as a non-admin fails with 403"

test_users_put_partial() {
    local user="$(unique_name usersputpartial)"
    create_user "$user" "pw_${RANDOM}" "Original Name" || { echo "setup failed"; return 1; }
    api PUT "/users/$user" "$ADMIN_KEY" '{"full_name":"Updated Name"}'
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" '"full_name":"Updated Name"' || return 1
    assert_contains "$BODY" '"is_admin":false'
}
register_test test_users_put_partial "PUT only updates given fields" \
    "PUT /users/{username} with only full_name leaves is_admin (and other fields) untouched"

test_users_put_email() {
    local user="$(unique_name usersputemail)"
    create_user "$user" "pw_${RANDOM}" || { echo "setup failed"; return 1; }
    api PUT "/users/$user" "$ADMIN_KEY" "{\"email\":\"$user@example.com\"}"
    assert_eq 200 "$STATUS" "status" || return 1
    assert_contains "$BODY" "\"email\":\"$user@example.com\""
}
register_test test_users_put_email "PUT can set a user's email" \
    "PUT /users/{username} with a well-formed email succeeds and the response shows the new email"

test_users_put_malformed_email() {
    local user="$(unique_name usersputbademail)"
    create_user "$user" "pw_${RANDOM}" || { echo "setup failed"; return 1; }
    api PUT "/users/$user" "$ADMIN_KEY" '{"email":"not-an-email"}'
    assert_eq 422 "$STATUS" "status"
}
register_test test_users_put_malformed_email "PUT rejects a malformed email" \
    "PUT /users/{username} with a syntactically invalid email fails with 422"

test_users_put_admin_remove_admin_flag() {
    api PUT /users/admin "$ADMIN_KEY" '{"is_admin":false}'
    assert_eq 400 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Cannot remove admin privileges from the admin user"
}
register_test test_users_put_admin_remove_admin_flag "admin user can't be demoted" \
    "PUT /users/admin with is_admin:false fails with 400, the admin user's admin flag is protected"

test_users_delete() {
    local user="$(unique_name usersdelete)"
    create_user "$user" "pw_${RANDOM}" || { echo "setup failed"; return 1; }
    api DELETE "/users/$user" "$ADMIN_KEY"
    assert_eq 204 "$STATUS" "status" || return 1
    api GET /users "$ADMIN_KEY"
    assert_not_contains "$BODY" "\"username\":\"$user\""
}
register_test test_users_delete "admin can delete a user" \
    "DELETE /users/{username} as admin returns 204 and the user no longer appears in GET /users"

test_users_delete_admin_rejected() {
    api DELETE /users/admin "$ADMIN_KEY"
    assert_eq 400 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Cannot delete the admin user"
}
register_test test_users_delete_admin_rejected "the admin user can't be deleted" \
    "DELETE /users/admin fails with 400, the admin user is non-removable"

test_users_delete_nonexistent() {
    api DELETE "/users/$(unique_name nosuchuser)" "$ADMIN_KEY"
    assert_eq 404 "$STATUS" "status"
}
register_test test_users_delete_nonexistent "deleting an unknown user is a 404" \
    "DELETE /users/{username} for a username that doesn't exist returns 404"
