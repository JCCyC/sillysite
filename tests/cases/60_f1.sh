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

test_teams_get_non_numeric_id() {
    api GET /teams/not-a-number "$ADMIN_KEY"
    assert_eq 404 "$STATUS" "status"
}
register_test test_teams_get_non_numeric_id "non-numeric team id is a 404" \
    "GET /teams/{id} with a non-numeric id 404s via route matching (the :int path converter), not 422 validation -- and isn't shadowed by /teams/winners"

test_team_winners() {
    api POST /teams "$ADMIN_KEY" '{"name":"Winner Team A","country":"Testland","founded_year":2000}'
    [ "$STATUS" = "201" ] || { echo "create team A failed: $STATUS $BODY"; return 1; }
    local team_a="$(json_get "$BODY" "['id']")"

    api POST /teams "$ADMIN_KEY" '{"name":"Winner Team B","country":"Testland","founded_year":2000}'
    [ "$STATUS" = "201" ] || { echo "create team B failed: $STATUS $BODY"; return 1; }
    local team_b="$(json_get "$BODY" "['id']")"

    api POST /teams "$ADMIN_KEY" '{"name":"Winless Team C","country":"Testland","founded_year":2000}'
    [ "$STATUS" = "201" ] || { echo "create team C failed: $STATUS $BODY"; return 1; }
    local team_c="$(json_get "$BODY" "['id']")"

    # Team A wins twice, team B wins once, team C never wins.
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":93,\"name\":\"Winners Test GP 1\",\"track_name\":\"Test Circuit\",\"winning_team_id\":$team_a}"
    [ "$STATUS" = "201" ] || { echo "create gp 1 failed: $STATUS $BODY"; return 1; }
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":94,\"name\":\"Winners Test GP 2\",\"track_name\":\"Test Circuit\",\"winning_team_id\":$team_a}"
    [ "$STATUS" = "201" ] || { echo "create gp 2 failed: $STATUS $BODY"; return 1; }
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":95,\"name\":\"Winners Test GP 3\",\"track_name\":\"Test Circuit\",\"winning_team_id\":$team_b}"
    [ "$STATUS" = "201" ] || { echo "create gp 3 failed: $STATUS $BODY"; return 1; }

    api GET /teams/winners "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get winners failed: $STATUS"; return 1; }

    python3 -c "
import json, sys
rows = json.loads(sys.argv[1])
a, b, c = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
by_id = {r['id']: r for r in rows}
assert a in by_id, f'team A ({a}) missing from winners list'
assert b in by_id, f'team B ({b}) missing from winners list'
assert c not in by_id, f'winless team C ({c}) unexpectedly in winners list'
assert by_id[a]['wins'] == 2, f\"team A wins: expected 2, got {by_id[a]['wins']}\"
assert by_id[b]['wins'] == 1, f\"team B wins: expected 1, got {by_id[b]['wins']}\"
ids = [r['id'] for r in rows]
assert ids.index(a) < ids.index(b), 'team A (2 wins) should rank above team B (1 win)'
" "$BODY" "$team_a" "$team_b" "$team_c"
    local rc=$?

    # Clean up so reruns against a persistent DB (the fast check's
    # container) don't collide with these fixed season/sequence_number
    # values. Grands-prix first: they FK-reference the teams.
    api DELETE /grands-prix/1999/93 "$ADMIN_KEY"
    api DELETE /grands-prix/1999/94 "$ADMIN_KEY"
    api DELETE /grands-prix/1999/95 "$ADMIN_KEY"
    api DELETE "/teams/$team_a" "$ADMIN_KEY"
    api DELETE "/teams/$team_b" "$ADMIN_KEY"
    api DELETE "/teams/$team_c" "$ADMIN_KEY"

    return "$rc"
}
register_test test_team_winners "team winners are ranked by win count" \
    "GET /teams/winners orders teams by total wins descending, omitting teams with zero wins"

test_team_winners_requires_auth() {
    api GET /teams/winners
    assert_eq 401 "$STATUS" "status"
}
register_test test_team_winners_requires_auth "team winners endpoint requires auth" \
    "GET /teams/winners with no apikey fails with 401"

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

test_driver_winners() {
    api POST /drivers "$ADMIN_KEY" '{"name":"Winner Driver A","nationality":"Testland","date_of_birth":"1990-01-01"}'
    [ "$STATUS" = "201" ] || { echo "create driver A failed: $STATUS $BODY"; return 1; }
    local driver_a="$(json_get "$BODY" "['id']")"

    api POST /drivers "$ADMIN_KEY" '{"name":"Winner Driver B","nationality":"Testland","date_of_birth":"1990-01-01"}'
    [ "$STATUS" = "201" ] || { echo "create driver B failed: $STATUS $BODY"; return 1; }
    local driver_b="$(json_get "$BODY" "['id']")"

    api POST /drivers "$ADMIN_KEY" '{"name":"Winless Driver C","nationality":"Testland","date_of_birth":"1990-01-01"}'
    [ "$STATUS" = "201" ] || { echo "create driver C failed: $STATUS $BODY"; return 1; }
    local driver_c="$(json_get "$BODY" "['id']")"

    # Driver A wins twice, driver B wins once, driver C never wins.
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":90,\"name\":\"Winners Test GP 4\",\"track_name\":\"Test Circuit\",\"winning_driver_id\":$driver_a}"
    [ "$STATUS" = "201" ] || { echo "create gp 4 failed: $STATUS $BODY"; return 1; }
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":91,\"name\":\"Winners Test GP 5\",\"track_name\":\"Test Circuit\",\"winning_driver_id\":$driver_a}"
    [ "$STATUS" = "201" ] || { echo "create gp 5 failed: $STATUS $BODY"; return 1; }
    api POST /grands-prix "$ADMIN_KEY" "{\"season\":1999,\"sequence_number\":92,\"name\":\"Winners Test GP 6\",\"track_name\":\"Test Circuit\",\"winning_driver_id\":$driver_b}"
    [ "$STATUS" = "201" ] || { echo "create gp 6 failed: $STATUS $BODY"; return 1; }

    api GET /drivers/winners "$ADMIN_KEY"
    [ "$STATUS" = "200" ] || { echo "get winners failed: $STATUS"; return 1; }

    python3 -c "
import json, sys
rows = json.loads(sys.argv[1])
a, b, c = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
by_id = {r['id']: r for r in rows}
assert a in by_id, f'driver A ({a}) missing from winners list'
assert b in by_id, f'driver B ({b}) missing from winners list'
assert c not in by_id, f'winless driver C ({c}) unexpectedly in winners list'
assert by_id[a]['wins'] == 2, f\"driver A wins: expected 2, got {by_id[a]['wins']}\"
assert by_id[b]['wins'] == 1, f\"driver B wins: expected 1, got {by_id[b]['wins']}\"
ids = [r['id'] for r in rows]
assert ids.index(a) < ids.index(b), 'driver A (2 wins) should rank above driver B (1 win)'
" "$BODY" "$driver_a" "$driver_b" "$driver_c"
    local rc=$?

    # Clean up so reruns against a persistent DB (the fast check's
    # container) don't collide with these fixed season/sequence_number
    # values. Grands-prix first: they FK-reference the drivers.
    api DELETE /grands-prix/1999/90 "$ADMIN_KEY"
    api DELETE /grands-prix/1999/91 "$ADMIN_KEY"
    api DELETE /grands-prix/1999/92 "$ADMIN_KEY"
    api DELETE "/drivers/$driver_a" "$ADMIN_KEY"
    api DELETE "/drivers/$driver_b" "$ADMIN_KEY"
    api DELETE "/drivers/$driver_c" "$ADMIN_KEY"

    return "$rc"
}
register_test test_driver_winners "driver winners are ranked by win count" \
    "GET /drivers/winners orders drivers by total wins descending, omitting drivers with zero wins"

test_driver_winners_requires_auth() {
    api GET /drivers/winners
    assert_eq 401 "$STATUS" "status"
}
register_test test_driver_winners_requires_auth "driver winners endpoint requires auth" \
    "GET /drivers/winners with no apikey fails with 401"

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
