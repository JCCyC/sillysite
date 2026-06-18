# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal FastAPI app used for testing website deployment. Core routes (auth, users,
whoami/logout, config) live in `main.py`; Formula One business logic (CRUD endpoints, `/about`,
`/season/{year}`) lives in `f1.py`, mounted as an `APIRouter`.

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
watches (`main.py`, `f1.py`, `auth.py`, `config.py`, `database.py`, `models.py`, `schemas.py`),
new pure-API tests belong in `tests/cases/10`–`70` so they're covered by the fast check too, not
only the full suite.

When writing or reviewing client code (Python/C/JS or otherwise) that checks an HTTP response
status, check against the endpoint's actual documented status rather than assuming `200`: `POST`
endpoints that create a resource return `201`, `DELETE` endpoints and `POST /change-password`
return `204` (no body). Prefer accepting the whole 2xx range (or the specific non-200 code that
endpoint actually returns) over a hardcoded `== 200` check.

## Git & Deployment

GitHub auth in this environment is unreliable (interactive gh flows and network timeouts fail);
prepare commits locally and let the user push manually.

## Architecture

- `main.py` defines the FastAPI app. `/` redirects (`307`) to `/login.html`, carrying along the
  caller's `X-API-Key`/`apikey` (header or query param) as an `apikey` query param if present. It
  also defines CRUD endpoints for `/users`, the `/login/challenge` and `/login/response`
  endpoints, a `/change-password` endpoint, a `/whoami` endpoint, a `/logout` endpoint, a
  `/config` endpoint, an `/activeusers` endpoint, a `/login.html` page, a `/whoami.html` page, a
  `/changepw.html` page, and serves `static/favicon.ico` at `/favicon.ico`. `PUT`
  endpoints accept partial bodies — only the fields provided are updated. On startup, default
  `app_config` rows (`session_ttl_seconds`, `login_timeout_seconds`, `change_pw_timeout_seconds`,
  `session_cleanup_interval_seconds`, `session_cleanup_grace_seconds`) are inserted if missing,
  and a non-removable `admin` user (id `0`, `is_admin=True`) is created if missing. An
  `@app.on_event("startup")` hook starts a background daemon thread that wakes up every
  `session_cleanup_interval_seconds` (`app_config`, default 15 minutes) and, in a single DB
  session, reads both config values and deletes any rows in `sessions` whose `expires_at` is more
  than `session_cleanup_grace_seconds` (`app_config`, default 1 hour) in the past. The thread is
  started from the startup hook rather than at module level specifically because `uvicorn
  --reload` imports `main.py` twice (once in the reloader process, once in the worker
  subprocess) — module-level side effects would start the thread twice, producing duplicate
  cleanup runs every cycle; the startup hook only fires once, inside the actual ASGI worker.
  Formula One routes are mounted via `app.include_router(f1.router)` (see `f1.py` below).

  Access control (see `auth.py`):
  - `/login/*`, `/`, `/about`, `/favicon.ico`, `/login.html`, `/whoami.html`, and `/changepw.html`
    are public.
  - `/change-password`, `/whoami`, and `/logout` require any logged-in user (`require_user`);
    `/change-password` changes that user's own password, `/whoami` returns information about
    that user and their session, and `/logout` invalidates the current session (by setting its
    `expires_at` to one millisecond in the past) and returns
    `{"msg": "User <username> logged out"}` — it fails with `400` if called with the static
    `.env` `API_KEY`, which has no session to invalidate.
  - `GET` on the Formula One endpoints requires any logged-in user (`require_user`).
  - Everything else (writes on Formula One data, all of `/users`, `GET /config`, and
    `GET /activeusers`) requires an admin (`require_admin`).
- `f1.py` holds all Formula One business logic, as a FastAPI `APIRouter` mounted by `main.py`:
  `/about` (returns `{"msg": "<random message>"}` chosen from a small list of candidate
  messages), CRUD endpoints for `/teams`, `/drivers` (keyed by `id`), `/driver-numbers` (keyed by
  the composite `driver_id`/`season`), and `/grands-prix/{season}/{sequence_number}` (keyed by
  the composite season/sequence number), and `GET /season/{year}` — returns all Grands Prix for
  that season in order, with the winning driver/team's *names* (not ids), 404 if the season has
  no races. It uses `joinedload` on `winning_driver`/`winning_team` to fetch each race's data in
  one query instead of issuing a separate `SELECT` per relationship per race (N+1).
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
- `c/` is a C client library (`libsillysite`, built via `make`) plus three CLI programs (`login`,
  `changepw`, `season`) mirroring `login.py`/`changepw.py`. Uses libcurl, OpenSSL
  (PBKDF2/HMAC), and cJSON. See `c/README-C.md`.
- `js/` is a JavaScript client library (`sillysite.js`, a dependency-free UMD module usable from
  Node via `require` or the browser via `<script>`) plus three Node CLI scripts (`login.js`,
  `logout.js`, `changepw.js`). In Node it uses the built-in `http`/`https`/`crypto` modules; in
  the browser it uses `fetch`/`crypto.subtle` (same APIs as `static/login.html`). See
  `js/README-JS.md`.

## Tests

`tests/run_tests.sh` is the single entry point covering the API itself, the Python utility
scripts, and the C and JS client bindings (72 tests as of this writing). Run it with no
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
whatever's already queued). Piping a password into `login.py`/`changepw.py` (used internally by
several test cases as a login helper, and tested directly themselves) needs `detached` (in
`tests/lib/proc.sh`, a thin `setsid` wrapper): Python's `getpass.getpass()` prefers `/dev/tty` over
stdin whenever a controlling terminal exists, so without it, running the suite from an interactive
shell makes those calls silently ignore the piped password and block on a real, unattended prompt
instead.

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
(`main.py`, `f1.py`, `auth.py`, `config.py`, `database.py`, `models.py`, `schemas.py`) and only
actually runs `fast_check.sh` if that hash changed since the last check (tracked in
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

`GET /login.html` serves `static/login.html`, a small login form that performs the login flow
above entirely in the browser using the Web Crypto API (`crypto.subtle` for PBKDF2 and
HMAC-SHA256), then redirects to `GET /whoami.html?apikey=<token>` with the resulting token. If the
request already carries a valid `X-API-Key`/`apikey` (header or query param, static or session),
no HTML is served — the endpoint instead redirects (`307`) to `GET /whoami.html?apikey=<that key>`.

## /whoami.html

`GET /whoami.html` serves `static/whoami.html`, styled consistently with `static/login.html`,
which fetches `GET /whoami` (using the `apikey` query parameter from its own URL, if present) and
displays the current user's information nicely, with a "Log out" link (using the same `apikey`)
shown if there's an associated session. If the request doesn't carry a valid `X-API-Key`/`apikey`
(header or query param, static or session), it redirects to `/login.html` instead.

## /changepw.html

`GET /changepw.html` serves `static/changepw.html`, styled consistently with `static/login.html`,
titled "Password change for `<username>`" (fetching `GET /whoami` to learn the username, using
the `apikey` query parameter from its own URL, if present). It has fields for the current
password, new password, and confirmation, and on submit performs the login flow (above) with the
current password to obtain a fresh session token, derives a new PBKDF2 salt/hash/iterations from
the new password, and submits those to `/change-password` via that token — entirely in the
browser, mirroring `changepw.py`. The result is shown as a styled message below the form (green
on success, red on error). If the request doesn't carry a valid `X-API-Key`/`apikey` (header or
query param, static or session), it redirects to `/login.html` instead.

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
