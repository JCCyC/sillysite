# Formula One CRUD endpoints and /season/{year}. Teams get full CRUD
# coverage; drivers/driver-numbers/grands-prix get a smoke test each, since
# they share the exact same access-control plumbing as teams.

test_teams_get_no_auth() {
    api GET /teams
    assert_eq 401 "$STATUS" "status"
}
register_test test_teams_get_no_auth "GET /teams requires auth" \
    "GET /teams with no apikey fails with 401"

test_teams_get_logged_in_non_admin() {
    new_logged_in_user teamsget || { echo "setup failed"; return 1; }
    api GET /teams "$TOKEN"
    assert_eq 200 "$STATUS" "status"
}
register_test test_teams_get_logged_in_non_admin "any logged-in user can GET teams" \
    "GET /teams as a non-admin logged-in user succeeds with 200"

test_teams_post_non_admin() {
    new_logged_in_user teamspostnonadmin || { echo "setup failed"; return 1; }
    api POST /teams "$TOKEN" '{"name":"Should Not Exist","country":"Nowhere","founded_year":2000}'
    assert_eq 403 "$STATUS" "status"
}
register_test test_teams_post_non_admin "creating a team requires admin" \
    "POST /teams as a non-admin fails with 403"

test_teams_full_crud() {
    api POST /teams "$ADMIN_KEY" '{"name":"Test Racing Team","country":"Testland","founded_year":2001}'
    [ "$STATUS" = "201" ] || { echo "create failed: $STATUS $BODY"; return 1; }
    local id="$(json_get "$BODY" "['id']")"
    [ -n "$id" ] || { echo "no id in response"; return 1; }

    api GET "/teams/$id" "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get failed: $STATUS"; return 1; }
    assert_contains "$BODY" '"name":"Test Racing Team"' || return 1

    api PUT "/teams/$id" "$ADMIN_KEY" '{"founded_year":2099}'
    [ "$STATUS" = "200" ] || { echo "put failed: $STATUS"; return 1; }
    assert_contains "$BODY" '"founded_year":2099' || return 1
    assert_contains "$BODY" '"name":"Test Racing Team"' || return 1

    api DELETE "/teams/$id" "$ADMIN_KEY"
    [ "$STATUS" = "204" ] || { echo "delete failed: $STATUS"; return 1; }

    api GET "/teams/$id" "$ADMIN_KEY"
    assert_eq 404 "$STATUS" "status after delete"
}
register_test test_teams_full_crud "teams: create, get, partial update, delete" \
    "POST/GET/PUT/DELETE /teams round-trip correctly, including that PUT only changes the given field and the team 404s after delete"

test_teams_get_unknown() {
    api GET /teams/99999999 "$ADMIN_KEY"
    assert_eq 404 "$STATUS" "status"
}
register_test test_teams_get_unknown "unknown team id is a 404" \
    "GET /teams/{id} for an id that doesn't exist returns 404"

test_drivers_smoke() {
    api POST /drivers "$ADMIN_KEY" '{"name":"Test Driver","nationality":"Testland","date_of_birth":"1995-01-01"}'
    [ "$STATUS" = "201" ] || { echo "create failed: $STATUS $BODY"; return 1; }
    local id="$(json_get "$BODY" "['id']")"

    api GET "/drivers/$id" "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get failed: $STATUS"; return 1; }

    api DELETE "/drivers/$id" "$ADMIN_KEY"
    assert_eq 204 "$STATUS" "delete status"
}
register_test test_drivers_smoke "drivers: create, get, delete" \
    "POST/GET/DELETE /drivers work end to end"

test_driver_numbers_smoke() {
    api POST /drivers "$ADMIN_KEY" '{"name":"Number Test Driver","nationality":"Testland","date_of_birth":"1995-01-01"}'
    [ "$STATUS" = "201" ] || { echo "driver create failed: $STATUS"; return 1; }
    local driver_id="$(json_get "$BODY" "['id']")"

    api POST /driver-numbers "$ADMIN_KEY" "{\"driver_id\":$driver_id,\"season\":1999,\"number\":99}"
    [ "$STATUS" = "201" ] || { echo "driver-number create failed: $STATUS $BODY"; return 1; }

    api GET "/driver-numbers/$driver_id/1999" "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get failed: $STATUS"; return 1; }
    assert_contains "$BODY" '"number":99' || return 1

    api DELETE "/driver-numbers/$driver_id/1999" "$ADMIN_KEY"
    assert_eq 204 "$STATUS" "delete status"
}
register_test test_driver_numbers_smoke "driver-numbers: create, get, delete" \
    "POST/GET/DELETE /driver-numbers (keyed by driver_id+season) work end to end"

test_grands_prix_smoke() {
    api POST /grands-prix "$ADMIN_KEY" '{"season":1999,"sequence_number":99,"name":"Test Grand Prix","track_name":"Test Circuit"}'
    [ "$STATUS" = "201" ] || { echo "create failed: $STATUS $BODY"; return 1; }

    api GET /grands-prix/1999/99 "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get failed: $STATUS"; return 1; }
    assert_contains "$BODY" '"name":"Test Grand Prix"' || return 1

    api DELETE /grands-prix/1999/99 "$ADMIN_KEY"
    assert_eq 204 "$STATUS" "delete status"
}
register_test test_grands_prix_smoke "grands-prix: create, get, delete" \
    "POST/GET/DELETE /grands-prix (keyed by season+sequence_number) work end to end"

test_season_known_year() {
    api GET /season/2014 "$ADMIN_KEY"
    assert_eq 200 "$STATUS" "status" || return 1
    local first_seq winner
    first_seq="$(json_get "$BODY" "[0]['sequence_number']")"
    winner="$(json_get "$BODY" "[0]['winning_driver']")"
    assert_eq 1 "$first_seq" "first race sequence_number" || return 1
    [ -n "$winner" ] && [ "$winner" != "None" ] || { echo "expected a winning_driver name, got: $winner"; return 1; }
}
register_test test_season_known_year "season/2014 lists races in order" \
    "GET /season/2014 returns 200 with races ordered by sequence_number, showing winner *names* (not ids)"

test_season_unknown_year() {
    api GET /season/1899 "$ADMIN_KEY"
    assert_eq 404 "$STATUS" "status" || return 1
    assert_contains "$BODY" "Season not found"
}
register_test test_season_unknown_year "season with no races is a 404" \
    "GET /season/{year} for a year with no Grands Prix returns 404 \"Season not found\""

test_season_requires_auth() {
    api GET /season/2014
    assert_eq 401 "$STATUS" "status"
}
register_test test_season_requires_auth "season endpoint requires auth" \
    "GET /season/{year} with no apikey fails with 401"
