# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal FastAPI app used for testing website deployment. All routes live in `main.py`.

## Commands

- Set up the virtual environment: `python3 -m venv .venv`
- Install dependencies: `.venv/bin/pip install -r requirements.txt`
- Run the dev server: `.venv/bin/uvicorn main:app --reload` (or `./run.sh`, which `cd`s to the repo root first)

## Architecture

- `main.py` defines the FastAPI app. `/` and `/about` each return
  `{"msg": "<random message>"}` chosen from a small list of candidate messages. It also defines
  CRUD endpoints for the Formula One data: `/teams`, `/drivers` (keyed by `id`), `/driver-numbers`
  (keyed by the composite `driver_id`/`season`), and `/grands-prix/{season}/{sequence_number}`
  (keyed by the composite season/sequence number), CRUD endpoints for `/users`, the
  `/login/challenge` and `/login/response` endpoints, a `/change-password` endpoint, a `/whoami`
  endpoint, a `/logout` endpoint, a `/config` endpoint, an `/activeusers` endpoint, a
  `/login.html` page, and serves `static/favicon.ico` at `/favicon.ico`. `PUT`
  endpoints accept partial bodies — only the fields provided are updated. On startup, default
  `app_config` rows (`session_ttl_seconds`, `login_timeout_seconds`, `change_pw_timeout_seconds`)
  are inserted if missing, and a non-removable `admin` user (id `0`, `is_admin=True`) is created
  if missing. A background daemon thread also wakes up every 15 minutes and deletes any rows in
  `sessions` whose `expires_at` is more than an hour in the past.

  Access control (see `auth.py`):
  - `/login/*`, `/`, `/about`, `/favicon.ico`, and `/login.html` are public.
  - `/change-password`, `/whoami`, and `/logout` require any logged-in user (`require_user`);
    `/change-password` changes that user's own password, `/whoami` returns information about
    that user and their session, and `/logout` invalidates the current session (by setting its
    `expires_at` to one second in the past) and returns
    `{"msg": "User <username> logged out"}` — it fails with `400` if called with the static
    `.env` `API_KEY`, which has no session to invalidate.
  - `GET` on the Formula One endpoints requires any logged-in user (`require_user`).
  - Everything else (writes on Formula One data, all of `/users`, `GET /config`, and
    `GET /activeusers`) requires an admin (`require_admin`).
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
  connecting to PostgreSQL and setting the schema search path.
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
  (all fields optional, used for `PUT` partial updates), plus the `User`/`UserCreate`/`UserUpdate`
  and login challenge/response schemas.
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

## /login.html

`GET /login.html` serves `static/login.html`, a small login form that performs the login flow
above entirely in the browser using the Web Crypto API (`crypto.subtle` for PBKDF2 and
HMAC-SHA256), then fetches and displays `GET /whoami` with the resulting token. If the request
already carries a valid `X-API-Key`/`apikey` (header or query param, static or session), no HTML
is served — the endpoint returns the `/whoami` result directly instead.
