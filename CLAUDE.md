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
  `/login/challenge` and `/login/response` endpoints, and serves `static/favicon.ico` at
  `/favicon.ico`. `GET` endpoints are public; `POST`/`PUT`/`DELETE` endpoints require an API key
  (see `auth.py`). `PUT` endpoints accept partial bodies — only the fields provided are updated.
  On startup, a default `session_ttl_seconds` row (3600) is inserted into `app_config` if missing.
- `auth.py` defines the `require_api_key` dependency, applied to all write (`POST`/`PUT`/`DELETE`)
  endpoints. It accepts either the static `X-API-Key` matching `config.API_KEY` (the admin
  credential), or a per-user session token issued via `/login/response` — session tokens are
  also checked against the `sessions` table for expiry and source IP. It also holds the password
  hashing (PBKDF2-HMAC-SHA256) and challenge/response helpers used by the login flow.
- `config.py` loads database connection settings (`DB_HOST`, `DB_PORT`, `DB_SCHEMA`, `DB_NAME`,
  `DB_USER`, `DB_PASSWORD`) and the `API_KEY` used for write-endpoint authentication from
  environment variables / a `.env` file (see `.env.example`).
- `database.py` configures the SQLAlchemy engine/session from the values in `config.py`,
  connecting to PostgreSQL and setting the schema search path.
- `models.py` defines the Formula One data model: `Team`, `Driver`, `DriverNumber`, and
  `GrandPrix`. A `Driver` holds a person's name, nationality, and date of birth; their car number
  for a given season is tracked separately in `DriverNumber` (since drivers can change numbers
  between seasons). `GrandPrix` records the winning driver and team directly (since drivers can
  change teams mid-season). It also defines `User` (username plus PBKDF2 salt/hash/iterations —
  never a plaintext password), `UserSession` (one-time login challenges and, once redeemed,
  the issued token, its expiry, and the source IP it's restricted to), and `AppConfig`
  (key/value settings, e.g. `session_ttl_seconds`). Tables are created automatically on startup
  via `Base.metadata.create_all`.
- `schemas.py` defines the Pydantic request/response models used by the CRUD endpoints,
  including `*Create` schemas (all fields required, used for `POST`) and `*Update` schemas
  (all fields optional, used for `PUT` partial updates), plus the `User`/`UserCreate` and
  login challenge/response schemas.
- `login.py` is a CLI script (`./login.py <url> <username>`) that prompts for a password,
  performs the challenge/response login flow, and prints the resulting session token to stdout
  (or an error to stderr).
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
   `{"token", "expires_at"}` on success (the challenge is single-use), or `403` on any failure
   (unknown user, expired/used challenge, wrong response).
4. The returned `token` can be used as the `X-API-Key` header value for write endpoints, but
   only from the source IP it was issued to, and only until `expires_at`.
