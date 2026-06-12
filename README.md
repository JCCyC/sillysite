# Silly Site
Test for website deployment

A FastAPI app with:
- `/`, which redirects to `/login.html` (passing along the caller's API key as `?apikey=`, if any)
- `/about`, which returns `{"msg": "<random message>"}`
- CRUD endpoints for Formula One data: `/teams`, `/drivers`, `/driver-numbers`, and
  `/grands-prix/{season}/{sequence_number}`, backed by PostgreSQL
- CRUD endpoints for `/users`, a challenge/response `/login` flow, and a `/change-password`
  endpoint
- A `/whoami` endpoint returning information about the logged-in user and their session
- A `/logout` endpoint that invalidates the current session and returns a confirmation message
  (fails for the static `API_KEY`)
- A `/config` endpoint (admin-only) listing the `app_config` settings
- An `/activeusers` endpoint (admin-only) listing active sessions: username, source IP, login
  time, and expiry time
- A `/login.html` page implementing the login flow in the browser
- A `/whoami.html` page showing the current user's `/whoami` info, styled like `/login.html`
- A `/changepw.html` page for changing the logged-in user's password, styled like `/login.html`
- `/favicon.ico`

All endpoints except `/`, `/about`, `/favicon.ico`, and `/login/*` require an `X-API-Key` header,
which can be either the static `API_KEY` configured in the environment (the `admin` user) or a
token obtained by logging in (see below). Instead of the header, the same value can be passed as
an `?apikey=...` query parameter; specifying both the header and the query parameter is treated
as if neither were provided.
- Logged-in non-admin users can make `GET` requests to the Formula One endpoints (`/teams`,
  `/drivers`, `/driver-numbers`, `/grands-prix`).
- Admins can do everything, including managing `/users`.

`PUT` endpoints accept partial bodies — only the fields provided are updated.

A Postman collection covering all endpoints is available in `postman_collection.json`.

## Endpoints

| Endpoint                                  | Methods                  |
| ------------------------------------------ | ------------------------- |
| `/`                                        | `GET`                     |
| `/about`                                   | `GET`                     |
| `/favicon.ico`                             | `GET`                     |
| `/login.html`                              | `GET`                     |
| `/whoami.html`                             | `GET`                     |
| `/changepw.html`                           | `GET`                     |
| `/teams`                                   | `GET`, `POST`             |
| `/teams/{team_id}`                         | `GET`, `PUT`, `DELETE`    |
| `/drivers`                                 | `GET`, `POST`             |
| `/drivers/{driver_id}`                     | `GET`, `PUT`, `DELETE`    |
| `/driver-numbers`                          | `GET`, `POST`             |
| `/driver-numbers/{driver_id}/{season}`     | `GET`, `PUT`, `DELETE`    |
| `/grands-prix`                             | `GET`, `POST`             |
| `/grands-prix/{season}/{sequence_number}`  | `GET`, `PUT`, `DELETE`    |
| `/users`                                   | `GET`, `POST`             |
| `/users/{username}`                        | `PUT`, `DELETE`           |
| `/login/challenge`                         | `POST`                    |
| `/login/response`                          | `POST`                    |
| `/change-password`                         | `POST`                    |
| `/whoami`                                  | `GET`                     |
| `/logout`                                  | `GET`                     |
| `/config`                                  | `GET`                     |
| `/activeusers`                             | `GET`                     |

## Logging in

After an admin creates a user via `POST /users`, that user can obtain a session token:

```bash
./login.py http://127.0.0.1:8000 <username>
Password:
```

If more than `login_timeout_seconds` (`app_config`, default 60) elapse between requesting the
challenge and submitting the response, the login fails with "Login timeout".

On success, the token is printed to stdout and can be used as the `X-API-Key` header. The token
is only valid from the IP address it was issued to, and expires after `session_ttl_seconds`
(1 hour by default, configurable in the `app_config` table).

Alternatively, `/login.html` serves a basic login page that performs this flow in the browser
and redirects to `/whoami.html?apikey=<token>` on success. If you visit it with a valid
`X-API-Key`/`apikey` already set, it skips the page and redirects to `/whoami.html?apikey=<that
key>` directly.

`/whoami.html` displays the same information as `/whoami`, styled like `/login.html`, with a
"Log out" link. It requires a valid `X-API-Key`/`apikey`, and redirects to `/login.html`
otherwise.

## Changing your password

A logged-in user can change their own password:

```bash
./changepw.py http://127.0.0.1:8000 <username>
Current password:
New password:
Confirm new password:
```

This logs in with the current password (as above), then submits a new PBKDF2 salt/hash/iteration
count derived locally from the new password — the new password itself is never sent over the
network. If `POST /change-password` arrives more than `change_pw_timeout_seconds` (`app_config`,
default 60) after the login completed, it fails with "Change password timeout". Requests made
with the static `.env` `API_KEY` aren't subject to this timeout, since they aren't tied to a login.

Alternatively, `/changepw.html` serves a basic "Password change for `<username>`" page, styled
like `/login.html`, that performs this same flow in the browser and shows the result as JSON
(`{"msg": ...}` or `{"detail": ...}`). It requires a valid `X-API-Key`/`apikey`, and redirects to
`/login.html` otherwise.

## Admin user

A non-removable `admin` user (id `0`) always exists, has `is_admin=True`, and a full name of
"System Administrator". Requests made with the `.env` `API_KEY` are treated as this user. It can
also have its own password set (via `PUT /users/admin`) and log in normally — both forms of
authentication work independently.

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
