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
