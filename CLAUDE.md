# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal FastAPI app used for testing website deployment. Core routes (auth, users,
whoami/logout, config) live in `main.py`; Formula One business logic (CRUD endpoints, `/about`,
`/season/{year}`) lives in `business.py`, mounted as an `APIRouter`.

## Adapting this template for a different business

The generic SaaS scaffolding (auth, sessions, users, admin, config, client bindings, test
framework, Docker deployment) has no Formula One knowledge at all — F1 exists only to give the
scaffolding something concrete to demonstrate. `business.py` is deliberately named generically:
to adapt this for a different business, replace its *contents* (and the matching pieces below),
not the file itself.

**Replace (F1-specific):**
- `business.py` — replace the F1 routes with your own (keep it mounted the same way in
  `main.py`: `app.include_router(business.router)`). Note `/about` currently lives here too —
  decide whether your replacement keeps a similar endpoint or drops it (see the test gotcha
  below if you drop it).
- `models.py` — keep `User`, `UserSession`, `AppConfig`; replace `Team`/`Driver`/`DriverNumber`/
  `GrandPrix` with your own tables.
- `schemas.py` — keep the `User*`, login/challenge/response, `ChangePasswordRequest`, `WhoAmI`,
  and `ActiveUser` schemas; replace the F1 schemas (`Team`, `Driver`, `DriverNumber`, `GrandPrix`,
  `SeasonGrandPrix`, `WinnerCount`) with your own.
- `seed.py` — replace with seed data for your own business, or remove (and drop `SEED_DB` support
  in `docker/entrypoint.sh`) if you don't need seeding.
- `tests/cases/60_business.sh` — replace with tests for your own business endpoints.
- `postman_collection.json`'s Teams/Drivers/Driver Numbers/Grands Prix/Season folders — replace
  with requests for your own endpoints.
- `static/favicon.ico` — cosmetic; swap for your own branding.
- The F1-specific parts of this file and `README.md` — the `business.py` architecture
  description, the Data Conventions section, and the season/winners endpoint docs.

**Test gotcha:** `tests/cases/10_public.sh`'s `test_about_public` expects `GET /about` to return
200 — but `/about` is defined in `business.py`. If your replacement doesn't keep an
`/about`-equivalent, remove that one test rather than leaving it to fail.

**Leave alone (generic, no F1 knowledge):**
- `main.py`, `auth.py`, `config.py`, `database.py` — the whole auth/session/user/admin/config
  system.
- `login.py`, `changepw.py`, all of `c/` (`login`/`changepw` only — deliberately no
  business-specific programs), all of `js/sillysite.js` and its three CLI scripts — the
  challenge/response login flow and change-password flow are business-agnostic.
- `static/login.html`, `static/whoami.html`, `static/changepw.html`, and `/sillysite.js`.
- `tests/lib/*`, `tests/run_tests.sh`, `tests/fast_check.sh`, `tests/hook_fast_check.sh`, and all
  of `tests/cases/` except `60_business.sh` — the generic test framework and coverage.
- `Dockerfile`, `docker/*` — the deployment story doesn't know or care what the business logic is.
- `.devcontainer/*` — the dev container setup doesn't know or care what the business logic is.

This repo is marked as a GitHub template repository (Settings → Template repository), so new
businesses should start via "Use this template" / `gh repo create --template` — a clean,
history-less copy, not a fork tied back here.

## Project Stack

This is a FastAPI (Python) project. Use a virtual environment (venv), and always verify database
integration after schema or seed data changes.

## Commands

- Set up the virtual environment: `python3 -m venv .venv`
- Install dependencies: `.venv/bin/pip install -r requirements.txt`
- Run the dev server: `.venv/bin/uvicorn main:app --reload` (or `./run.sh`, which `cd`s to the repo root first)

## Data Conventions

Use F1-themed seed data with years ranging 2014-2025 (do not assume 2026 or future data unless
explicitly requested).

## Workflow

After implementing endpoints or features, run tests/verify the change and update docs and
Postman collection accordingly. "Docs" explicitly includes this file (`CLAUDE.md`) — whenever a
change alters the architecture, an endpoint's behavior, a file's responsibilities, or adds a new
directory/module, update the relevant `CLAUDE.md` section in the same change, not as a separate
follow-up later. Treat `CLAUDE.md` drift as a bug, the same way you'd treat a failing test.

This also applies to the test suite (`tests/`): whenever a change adds an endpoint, changes an
endpoint's behavior or status code, or adds/changes a utility script or client binding, add or
update the corresponding `tests/cases/*.sh` test(s) in the same change — not as a follow-up, and
not only when explicitly asked. A passing suite that doesn't actually cover the new behavior is
worse than an honestly failing one. If the change touches one of the files `tests/hook_fast_check.sh`
watches (`main.py`, `business.py`, `auth.py`, `config.py`, `database.py`, `models.py`,
`schemas.py`), new pure-API tests belong in `tests/cases/10`–`70` so they're covered by the fast
check too, not only the full suite.

When writing or reviewing client code (Python/C/JS or otherwise) that checks an HTTP response
status, check against the endpoint's actual documented status rather than assuming `200`: `POST`
endpoints that create a resource return `201`, `DELETE` endpoints and `POST /change-password`
return `204` (no body). Prefer accepting the whole 2xx range (or the specific non-200 code that
endpoint actually returns) over a hardcoded `== 200` check.

Route registration order should never matter — when adding a path parameter, use the narrowest
Starlette converter the value's type actually supports (`{id:int}`, `{id:uuid}`, etc.) rather than
a bare `{name}`, so a literal sibling route (e.g. `/drivers/winners` next to
`/drivers/{driver_id}`) can never be shadowed regardless of which is registered first — see
`business.py`. This isn't fully achievable for string-typed parameters with no narrower natural type
(`/users/{username}` in `main.py`, since usernames have no fixed format to constrain): there's
currently no literal route under `/users/` for it to collide with, but if one is ever added,
register it before `/users/{username}` and double-check for this exact class of shadowing, since
order is the only lever available there.

## Git & Deployment

GitHub auth in this environment is unreliable (interactive gh flows and network timeouts fail);
prepare commits locally and let the user push manually.

## Architecture

- `main.py` defines the FastAPI app. `/` redirects (`307`) to `/login.html`, carrying along the
  caller's `X-API-Key`/`apikey` (header or query param) as an `apikey` query param if present. It
  also defines CRUD endpoints for `/users`, the `/login/challenge` and `/login/response`
  endpoints, a `/change-password` endpoint, a `/whoami` endpoint, a `/logout` endpoint, a
  `/config` endpoint, an `/activeusers` endpoint, a `/login.html` page, a `/whoami.html` page, a
  `/changepw.html` page, serves `static/favicon.ico` at `/favicon.ico`, and serves `js/sillysite.js`
  at `/sillysite.js` (so `static/login.html`/`static/whoami.html`/`static/changepw.html` can load
  it via a plain `<script src="/sillysite.js">` tag instead of duplicating its crypto/login logic
  inline). `PUT`
  endpoints accept partial bodies — only the fields provided are updated. On startup, default
  `app_config` rows (`session_ttl_seconds`, `login_timeout_seconds`, `change_pw_timeout_seconds`,
  `session_cleanup_interval_seconds`, `session_cleanup_grace_seconds`) are inserted if missing,
  and a non-removable `admin` user (id `0`, `is_admin=True`) is created if missing. This logic
  runs at module level (once per worker process, not behind a startup hook — it has to run before
  the rest of import-time setup), so under `gunicorn` with `WEB_CONCURRENCY>1` multiple workers
  can race to insert the same row on a cold start; the insert-then-commit for each is wrapped in
  its own `try`/`except IntegrityError` (rollback and move on) rather than a single batch commit,
  since whichever worker loses the race finding the row already there is exactly the desired
  outcome, not an error. A `lifespan` async context manager (passed to `FastAPI(lifespan=...)`,
  the non-deprecated replacement for `@app.on_event("startup")`) starts a background daemon
  thread on entry that wakes up every `session_cleanup_interval_seconds` (`app_config`, default
  15 minutes) and, in a single DB session, reads both config values and deletes any rows in
  `sessions` whose `expires_at` is more than `session_cleanup_grace_seconds` (`app_config`,
  default 1 hour) in the past. The thread is started from `lifespan` rather than at module level
  specifically because `uvicorn --reload` imports `main.py` twice (once in the reloader process,
  once in the worker subprocess) — module-level side effects would start the thread twice,
  producing duplicate cleanup runs every cycle; `lifespan` only runs once, inside the actual ASGI
  worker.
  Formula One routes are mounted via `app.include_router(business.router)` (see `business.py`
  below).

  Access control (see `auth.py`):
  - `/login/*`, `/`, `/about`, `/favicon.ico`, `/sillysite.js`, `/login.html`, `/whoami.html`, and
    `/changepw.html` are public.
  - `/change-password`, `/whoami`, and `/logout` require any logged-in user (`require_user`);
    `/change-password` changes that user's own password, `/whoami` returns information about
    that user and their session, and `/logout` invalidates the current session (by setting its
    `expires_at` to one millisecond in the past) and returns
    `{"msg": "User <username> logged out"}` — it fails with `400` if called with the static
    `.env` `API_KEY`, which has no session to invalidate.
  - `GET` on the Formula One endpoints requires any logged-in user (`require_user`).
  - Everything else (writes on Formula One data, all of `/users`, `GET /config`, and
    `GET /activeusers`) requires an admin (`require_admin`).
- `business.py` holds all Formula One business logic, as a FastAPI `APIRouter` mounted by
  `main.py`:
  `/about` (returns `{"msg": "<random message>"}` chosen from a small list of candidate
  messages), CRUD endpoints for `/teams`, `/drivers` (keyed by `id`), `/driver-numbers` (keyed by
  the composite `driver_id`/`season`), and `/grands-prix/{season}/{sequence_number}` (keyed by
  the composite season/sequence number), and `GET /season/{year}` — returns all Grands Prix for
  that season in order, with the winning driver/team's *names* (not ids), 404 if the season has
  no races. It uses `joinedload` on `winning_driver`/`winning_team` to fetch each race's data in
  one query instead of issuing a separate `SELECT` per relationship per race (N+1). `GET
  /drivers/winners` and `GET /teams/winners` return drivers/teams that have won at least one
  Grand Prix (across all seasons), each as `{"id", "name", "wins"}`, ordered by `wins` descending
  (ties broken alphabetically by name); winless drivers/teams are omitted, which falls out
  naturally from an inner join against `grands_prix` rather than needing an explicit filter. Every
  numeric path parameter in this file (`{team_id:int}`, `{driver_id:int}`, `{season:int}`,
  `{sequence_number:int}`, `{year:int}`) uses Starlette's `:int` path converter rather than a bare
  `{name}`, which constrains route *matching* itself to digit-only segments — not just Pydantic
  validation after the fact — so a literal sibling route like `/drivers/winners` is never shadowed
  by `/drivers/{driver_id:int}` regardless of registration order (a non-numeric segment like
  `/drivers/abc` now 404s rather than 422, since it never matches that route at all).
- `auth.py` resolves the caller's `User` from the `X-API-Key` header or an `apikey` query
  parameter (`resolve_api_key`; if both are present, the request is treated as unauthenticated,
  even if they match): either the static key matching `config.API_KEY` (which maps to the `admin`
  user, id `0` — so that user's own password, if set, also works independently via `/login`), or
  a session token issued by `/login/response` (checked against the `sessions` table for expiry
  and source IP). `require_user` requires any authenticated user; `require_admin` additionally
  requires `is_admin`. `get_current_session` resolves the `UserSession` behind a session token
  (returning `None` for the static API key), used by `/change-password` for its timeout check. It
  also holds the password hashing (PBKDF2-HMAC-SHA256) and challenge/response helpers used by the
  login flow.
- `config.py` loads database connection settings (`DB_HOST`, `DB_PORT`, `DB_SCHEMA`, `DB_NAME`,
  `DB_USER`, `DB_PASSWORD`) and the `API_KEY` used for write-endpoint authentication from
  environment variables / a `.env` file (see `.env.example`).
- `database.py` configures the SQLAlchemy engine/session from the values in `config.py`,
  connecting to PostgreSQL and setting the schema search path. Set `SQL_ECHO=1` in the
  environment to log every SQL query the engine issues (useful for spotting N+1 queries).
- `models.py` defines the Formula One data model: `Team`, `Driver`, `DriverNumber`, and
  `GrandPrix`. A `Driver` holds a person's name, nationality, and date of birth; their car number
  for a given season is tracked separately in `DriverNumber` (since drivers can change numbers
  between seasons). `GrandPrix` records the winning driver and team directly (since drivers can
  change teams mid-season). It also defines `User` (username, full name, `is_admin` flag, plus PBKDF2
  salt/hash/iterations — never a plaintext password), `UserSession` (one-time login challenges
  and, once redeemed, the issued token, its expiry, the source IP it's restricted to, and
  `authenticated_at`, the time the token was issued), and `AppConfig` (key/value settings, e.g.
  `session_ttl_seconds`). Tables are created automatically on startup via
  `Base.metadata.create_all`.
- `schemas.py` defines the Pydantic request/response models used by the CRUD endpoints,
  including `*Create` schemas (all fields required, used for `POST`) and `*Update` schemas
  (all fields optional, used for `PUT` partial updates), the `User`/`UserCreate`/`UserUpdate`
  and login challenge/response schemas, and `SeasonGrandPrix` (the `/season/{year}` response
  shape: sequence number, name, track name, and winning driver/team *names*).
- `login.py` is a CLI script (`./login.py <url> <username>`) that prompts for a password,
  performs the challenge/response login flow, and prints the resulting session token to stdout
  (or an error to stderr).
- `changepw.py` is a CLI script (`./changepw.py <url> <username>`) that prompts for the current
  password, a new password, and a confirmation of the new password, logs in with the current
  password (also used as the change-password timing reference), derives a new PBKDF2
  salt/hash/iterations from the new password, and submits those to `/change-password` (so the
  new password is never sent over the network).
- `seed.py` is a one-off script that populates the database with Formula One season data from
  2014 through 2025 (run with `.venv/bin/python seed.py`).
- `postman_collection.json` is a Postman collection covering all endpoints, with `base_url` and
  `api_key` collection variables for testing the API.
- `c/` is a C client library (`libsillysite`, built via `make`) plus two CLI programs (`login`,
  `changepw`) mirroring `login.py`/`changepw.py` — deliberately no business-specific programs.
  Uses libcurl, OpenSSL (PBKDF2/HMAC), and cJSON. See `c/README-C.md`.
- `js/` is a JavaScript client library (`sillysite.js`, a dependency-free UMD module usable from
  Node via `require` or the browser via `<script>`) plus three Node CLI scripts (`login.js`,
  `logout.js`, `changepw.js`). In Node it uses the built-in `http`/`https`/`crypto` modules; in
  the browser it uses `fetch`/`crypto.subtle`. `main.py` also serves it directly to the browser at
  `/sillysite.js`, and `static/login.html`/`static/whoami.html`/`static/changepw.html` load it via
  `<script src="/sillysite.js">` and call its functions rather than duplicating login/crypto logic
  inline. See `js/README-JS.md`.

## Tests

`tests/run_tests.sh` is the single entry point covering the API itself, the Python utility
scripts, the C and JS client bindings, and the static browser pages (76 tests as of this
writing). Run it with no
arguments: it builds a fresh `sillysite-test` Docker image, starts it as a container (seeded via
`SEED_DB=true`, fixed test `API_KEY`, on the first free port from `19700`), runs every test
against that container, and writes a full report to `tests/report.txt` (live progress also
prints to the terminal as `#N (short description)... PASS`/`FAIL`). On success it removes the
container and image it created; on failure it leaves them running for post-mortem (`docker
logs`/`docker exec`) and refuses to start a new run while a same-named leftover container exists,
to avoid clobbering that post-mortem state. The same applies if the run is interrupted (Ctrl-C,
crash, or a hang) before it reaches that cleanup-or-postmortem step — the container is left
running either way, and the next run will refuse to start until it's removed by hand:
`docker rm -f -v sillysite-test` (add `docker rmi sillysite-test` to also drop the image). Test
cases live in `tests/cases/*.sh` (sourced in
order; each calls `register_test` with a function, a short description, and a longer one), backed
by shared helpers in `tests/lib/`: `framework.sh` (registry/runner/assertions), `api.sh`
(HTTP + JSON helpers, user/login helpers), `docker.sh` (image/container lifecycle, `app_config`
DB tweaks for the login/change-password timeout tests), and `proc.sh` (driving the Python/C/JS
clients as subprocesses). The C client reads passwords from `/dev/tty`, not stdin, so driving it
non-interactively needs a real controlling terminal — `tests/lib/pty_drive.py` spawns it under a
pty and feeds scripted prompt/answer pairs at the right time (sending too early loses the input,
since the C client's `tcsetattr(..., TCSAFLUSH, ...)` when entering no-echo mode discards
whatever's already queued). `tests/cases/97_static_pages.sh` drives a real headless Chrome through
`static/login.html` → `static/whoami.html` → `static/changepw.html` → re-login over the plain
WebDriver HTTP protocol (`tests/lib/browser_e2e.py`, using just `chromedriver` + stdlib
`urllib` — no selenium/puppeteer needed); it's the only test exercising the *browser* code path of
`js/sillysite.js` (`fetch`/`crypto.subtle`), since the JS binding tests only exercise the Node code
path. `chromedriver` is a preflight requirement for `run_tests.sh`; this test isn't part of
`fast_check.sh`'s subset (real browser startup is too slow for a per-turn check). Piping a
password into `login.py`/`changepw.py` (used internally by several test cases as a login helper,
and tested directly themselves) needs `detached` (in
`tests/lib/proc.sh`, a thin `setsid` wrapper): Python's `getpass.getpass()` prefers `/dev/tty` over
stdin whenever a controlling terminal exists, so without it, running the suite from an interactive
shell makes those calls silently ignore the piped password and block on a real, unattended prompt
instead.

### Running tests from inside the Dev Container

Both `tests/run_tests.sh` and `tests/fast_check.sh` start sidecar Docker containers
(`sillysite-test`, `sillysite-fastdb`) and then talk to them as `127.0.0.1:<published-port>`.
That works fine on a bare host, but not when the test script is itself running inside
`.devcontainer`'s `app` service: `app`'s Docker access is Docker-outside-of-Docker (the host's
rootless dockerd, reached over a bind-mounted socket — see "Dev container" below), so `docker run
-p 127.0.0.1:PORT:...` publishes that port on the *host's* loopback, which is a different network
namespace from `app`'s own — unreachable as `127.0.0.1` from inside `app` even though the sidecar
container is perfectly healthy. `own_container_network` (`tests/lib/docker.sh`) detects this (via
`/.dockerenv` plus `docker inspect "$(hostname)"`, which works because Docker sets a container's
hostname to its own short ID by default) and returns the docker network `app` itself is attached
to, or nothing if not running in a container. When it returns a network, `start_container`
(`tests/lib/docker.sh`) and `ensure_fastdb_running` (`tests/lib/fastdb.sh`) attach the sidecar
container to that same network instead, and callers address it by container name (Docker's
embedded DNS resolves container names within a user-defined bridge network) rather than via the
host-published port: `run_tests.sh` sets `BASE_URL=http://sillysite-test:8000`, and
`fast_check.sh` sets `DB_HOST`/`DB_PORT` from `fastdb.sh`'s `$FASTDB_HOST`/`$FASTDB_DB_PORT`
(`sillysite-fastdb`/`5432`) instead of `127.0.0.1`/`$FASTDB_PORT`. The host-published port mapping
and `$FASTDB_PORT`/`$TEST_PORT` host port allocation are still kept either way, so a plain host
shell can still reach the same container directly — only the *address the test runner itself
connects to* changes. One more wrinkle specific to `tests/cases/97_static_pages.sh`: a container
name like `http://sillysite-test:8000` isn't a "secure context" to a real browser (only `https:`,
or the special-cased `http://localhost`/`http://127.0.0.1`, qualify), so `window.crypto.subtle`
(used by `/sillysite.js`) would silently be missing and the login flow would fail with no
exception — `tests/lib/browser_e2e.py` works around this by launching Chrome with
`--unsafely-treat-insecure-origin-as-secure=<base_url>`, which tells Chrome to treat that one
origin as secure for the test session regardless.

### Fast check (`tests/fast_check.sh`)

A lighter, much faster alternative to `tests/run_tests.sh` for everyday iteration: it reuses a
persistent Postgres-only container (`sillysite-fastdb`, built from the same image but with
supervisord/gunicorn skipped in favor of running Postgres directly, seeded once and left running
across calls) and runs the API natively via the project's own venv (`.venv/bin/uvicorn`) straight
from the current source tree — no image rebuild, no reseeding — against the pure-API test cases
only (`tests/cases/10`–`70`; the Python-script and C/JS-binding cases are skipped, since they add
subprocess overhead and rarely break from typical app-code edits). Takes a few seconds once the
fastdb container exists, versus minutes for the full suite. It is *not* a substitute for
`tests/run_tests.sh` — that remains the authoritative, full-coverage check to run before
considering a feature done. The fastdb container's data isn't reset between calls, so harmless
test rows accumulate over time; `docker rm -f -v sillysite-fastdb` to start clean.

`tests/hook_fast_check.sh` wraps it for automatic use: it hashes a fixed list of watched app files
(`main.py`, `business.py`, `auth.py`, `config.py`, `database.py`, `models.py`, `schemas.py`) and
only actually runs `fast_check.sh` if that hash changed since the last check (tracked in
`tests/.fast_check_hash`), so it's a no-op on turns that didn't touch app code. It stays silent on
a pass, and on a failure prints a `systemMessage` JSON line (pass/fail counts, pointers to
`tests/fast_report.txt` and the full suite) — it never blocks the turn from ending. This is wired
up as an async `Stop` hook in `.claude/settings.local.json` (personal/untracked, not the committed
`.claude/settings.json` — the hook is a local convenience, not a team-wide requirement; the
underlying scripts it calls are committed and shared either way).

## Login flow

1. `POST /login/challenge` with `{"username": ...}` returns a one-time `challenge`, the user's
   PBKDF2 `salt` and `iterations` (a random salt/default iterations are returned for unknown
   usernames too, so the response shape doesn't leak which usernames exist).
2. The client derives `key = PBKDF2-HMAC-SHA256(password, salt, iterations)` and computes
   `response = HMAC-SHA256(key, challenge)`.
3. `POST /login/response` with `{"username", "challenge", "response"}` returns
   `{"token", "expires_at"}` on success (the challenge is single-use), or `403` on any failure:
   `"Login timeout"` if more than `login_timeout_seconds` (`app_config`, default 60) elapsed
   since the challenge was issued, or a generic `"Invalid username or password"` for any other
   failure (unknown user, reused challenge, wrong response).
4. The returned `token` can be used as the `X-API-Key` header value, but only from the source IP
   it was issued to, and only until `expires_at`. What it grants access to depends on the user's
   `is_admin` flag (see access control above).

## Change password flow

1. The user logs in normally (see above), obtaining a session token.
2. The client derives a fresh PBKDF2 salt/hash/iterations from the new password locally.
3. `POST /change-password` with `{"new_salt", "new_password_hash", "new_iterations"}` (using the
   session token as `X-API-Key`) overwrites the caller's stored password credentials — the new
   password itself is never transmitted.
4. If the request arrives more than `change_pw_timeout_seconds` (`app_config`, default 60) after
   the session's token was issued (`UserSession.authenticated_at`), it fails with `403`
   `"Change password timeout"`. Requests authenticated with the static `.env` `API_KEY` have no
   associated session and are not subject to this timeout.
5. Regardless of success or failure, if the request was authenticated with a session token, that
   session's `expires_at` is immediately set to one millisecond in the past — the session created
   to authorize the password change is single-use and doesn't linger as active afterward.

## /login.html

`GET /login.html` serves `static/login.html`, a small login form that loads `/sillysite.js` and
calls `SillySite.login(window.location.origin, username, password)` to perform the login flow
above entirely in the browser (via the Web Crypto API, same as the rest of the library), then
redirects to `GET /whoami.html?apikey=<token>` with the resulting token. If the request already
carries a valid `X-API-Key`/`apikey` (header or query param, static or session), no HTML is served
— the endpoint instead redirects (`307`) to `GET /whoami.html?apikey=<that key>`.

## /whoami.html

`GET /whoami.html` serves `static/whoami.html`, styled consistently with `static/login.html`,
which loads `/sillysite.js` and calls `SillySite.get(window.location.origin, apikey, "/whoami")`
(using the `apikey` query parameter from its own URL, if present) and displays the current user's
information nicely, with a "Log out" link (using the same `apikey`) shown if there's an associated
session. If the request doesn't carry a valid `X-API-Key`/`apikey` (header or query param, static
or session), it redirects to `/login.html` instead.

## /changepw.html

`GET /changepw.html` serves `static/changepw.html`, styled consistently with `static/login.html`,
titled "Password change for `<username>`" (fetching `GET /whoami` via `SillySite.get` to learn the
username, using the `apikey` query parameter from its own URL, if present). It has fields for the
current password, new password, and confirmation, and on submit calls
`SillySite.changepw(window.location.origin, username, currentPassword, newPassword)` — same
library call `changepw.py`/`changepw.js`/`c/changepw` use, entirely in the browser this time. The
result is shown as a styled message below the form (green on success, red on error). If the
request doesn't carry a valid `X-API-Key`/`apikey` (header or query param, static or session), it
redirects to `/login.html` instead.

## Docker deployment

`Dockerfile` (based on `debian:stable`) packages the API and its PostgreSQL database into a
single image, started via `docker/entrypoint.sh` and managed by `supervisord`
(`docker/supervisord.conf`): `postgres`, the API (`gunicorn` with `uvicorn.workers.UvicornWorker`,
worker count via `WEB_CONCURRENCY`), and `docker/db-size-monitor.sh` (enforces
`DB_SIZE_LIMIT_MB` by toggling `default_transaction_read_only` on the database). On first run,
`entrypoint.sh` initializes the PostgreSQL data directory (on the `pgdata` volume), creates the
`DB_USER`/`DB_NAME` role/database, and generates/persists a random `DB_PASSWORD` and `API_KEY` in
`/var/lib/sillysite/secrets.env` (on the `state` volume) if not provided. `docker/deploy.sh` (with
settings from `docker/deploy.env`, see `docker/deploy.env.example`) builds the image and runs the
container with the configured port mappings (API port, optional PostgreSQL port) and resource
limits (`--memory`, `--cpus`, falling back to no CPU limit if the host doesn't support it). See
`docker/DEPLOY.md` for end-user deployment instructions.

## Dev container

`.devcontainer/` provides a VS Code Dev Containers setup for local development, independent of
the `Dockerfile`/`docker/` production deployment story above. `.devcontainer/devcontainer.json`
configures a multi-service `docker-compose` setup (`.devcontainer/docker-compose.yml`): an `app`
service (built from `.devcontainer/Dockerfile`, layering Python, the C/JS toolchains, the `docker`
CLI, and a headless Chromium browser for the static-pages test on top of the standard
`mcr.microsoft.com/devcontainers/base:debian-12` image) and a `db` service (plain `postgres:16`,
configured via `environment:` so no `.env` file is needed inside the container — `config.py`'s
`load_dotenv()` doesn't override already-set environment variables). One official Feature
(`ghcr.io/devcontainers/features/node:1`) adds Node.js on top of the built image.
`.devcontainer/post-create.sh` runs once on container creation: installs the Claude Code CLI
(`npm install -g @anthropic-ai/claude-code`; the `anthropic.claude-code` VS Code extension is
also in `devcontainer.json`'s `customizations.vscode.extensions`), sets up the Python venv, waits
for Postgres, creates tables (`import main`), seeds sample data, and builds the C client.
"Once" means once per *container* creation, not once ever — "Rebuild Container" recreates the
container but keeps the named `db` volume from any previous run, so `postCreateCommand` (and
this script) runs again against an already-seeded database. `seed.py` itself has no such
guard (it's meant to be simple — see "Adapting this template" above), so the script checks
whether any `Team` rows already exist before calling it, skipping with a log message if so,
rather than crashing on a duplicate-key `IntegrityError` on the second run.
`docker-compose.yml` also bind-mounts the host's `~/.claude` to `/root/.claude` so Claude Code is
already logged in inside the container, sharing settings/memory with the host rather than
needing a separate login.

The `app` service's Docker access (so `tests/run_tests.sh`, which itself drives Docker, can run
*inside* the dev container, talking to the same daemon as the host rather than a nested one) is
hand-rolled rather than using the official `ghcr.io/devcontainers/features/docker-outside-of-docker`
Feature, because that Feature doesn't work on this machine and can't be made to from project
files alone — worth understanding both gotchas below in case either bites on a different host:

- That Feature always declares its own mount of the host's `/var/run/docker.sock` to
  `/var/run/docker-host.sock` inside the container, regardless of anything declared in this
  project's own `docker-compose.yml` — confirmed by replaying the actual 3-file compose merge
  VS Code generates (`docker compose -f <ours> -f <vscode build override> -f <vscode
  containerFeatures override> config`): a same-target mount declared in our own file is
  discarded, since the Feature's auto-generated override is merged in last and always wins. This
  host runs **rootless** Docker, whose real socket lives at `/run/user/<uid>/docker.sock` (check
  `docker context inspect --format '{{.Endpoints.docker.Host}}'`) rather than the conventional
  `/var/run/docker.sock` the Feature hardcodes, so its auto-mount always fails to resolve and the
  container never starts. Dropping the Feature and installing `docker.io` directly in the
  Dockerfile instead sidesteps it entirely: `docker-compose.yml`'s own mount of the real rootless
  socket to the conventional in-container path is then the *only* mount involved, and nothing
  auto-generated can override it.
- `remoteUser` is `root`, not the base image's non-root `vscode` user. Rootless Docker maps
  container UID 0 transparently to the real host user (the one running the rootless daemon), but
  maps any *other* container UID into an unrelated subordinate range (`/etc/subuid`) — so a
  non-root user has no real relationship to files the host user owns in the bind-mounted
  workspace, even though both may show as the same UID number inside the container. Confirmed
  directly: `touch` on a file already in the bind-mounted workspace succeeded as root but failed
  with `Permission denied` as `vscode`, despite `id` showing both as UID 1000. This is safe
  specifically because Docker is rootless here: container root carries no more host privilege
  than the unprivileged user already running the daemon.

One thing in `.devcontainer/docker-compose.yml` is hardcoded to a specific machine and needs
adjusting on a different host: the workspace bind mount path matches the host's checkout path
exactly (instead of a generic `/workspace`), because the `docker` CLI inside the container talks
to the *host's* daemon — any bind-mount/build-context path it's given (e.g. by
`tests/run_tests.sh`) is resolved against the host's filesystem, not the container's view of it,
so the path has to be identical on both sides for that to work. The Docker socket source path
(`/run/user/<uid>/docker.sock`) is similarly specific to this rootless setup and needs checking
on a different host (same `docker context inspect` command as above) — a conventional rootful
host would mount the standard `/var/run/docker.sock` instead.
