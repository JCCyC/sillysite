# Silly Site
Test for website deployment

A FastAPI app with:
- `/` and `/about`, which each return `{"msg": "<random message>"}`
- CRUD endpoints for Formula One data: `/teams`, `/drivers`, `/driver-numbers`, and
  `/grands-prix/{season}/{sequence_number}`, backed by PostgreSQL
- CRUD endpoints for `/users` and a challenge/response `/login` flow
- `/favicon.ico`

All endpoints except `/`, `/about`, `/favicon.ico`, and `/login/*` require an `X-API-Key` header,
which can be either the static `API_KEY` configured in the environment (the `admin` user) or a
token obtained by logging in (see below):
- Logged-in non-admin users can make `GET` requests to the Formula One endpoints (`/teams`,
  `/drivers`, `/driver-numbers`, `/grands-prix`).
- Admins can do everything, including managing `/users`.

`PUT` endpoints accept partial bodies — only the fields provided are updated.

A Postman collection covering all endpoints is available in `postman_collection.json`.

## Logging in

After an admin creates a user via `POST /users`, that user can obtain a session token:

```bash
./login.py http://127.0.0.1:8000 <username>
Password:
```

On success, the token is printed to stdout and can be used as the `X-API-Key` header. The token
is only valid from the IP address it was issued to, and expires after `session_ttl_seconds`
(1 hour by default, configurable in the `app_config` table).

## Admin user

A non-removable `admin` user (id `0`) always exists and has `is_admin=True`. Requests made with
the `.env` `API_KEY` are treated as this user. It can also have its own password set (via
`PUT /users/admin`) and log in normally — both forms of authentication work independently.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# edit .env to set DB connection details and API_KEY
```

## Running

```bash
.venv/bin/uvicorn main:app --reload
```

or `./run.sh`, which `cd`s to the repo root first.

## Seeding data

```bash
.venv/bin/python seed.py
```

populates the database with Formula One season data from 2014 through 2025.
