# Deploying Silly Site

This directory contains everything needed to run the API and its PostgreSQL
database in a single Docker container.

## Prerequisites

- Docker installed and working (`docker version`).

## 1. Configure

```bash
cp deploy.env.example deploy.env
```

Edit `deploy.env` to taste. The available settings are documented in the file
itself:

- `API_PORT` — host port for the API (default `19505`)
- `EXPOSE_POSTGRES` — `yes`/`no`, whether PostgreSQL is reachable from the host
  (default `no`)
- `POSTGRES_PORT` — host port for PostgreSQL, if exposed (default `55432`)
- `MEMORY_LIMIT` — container RAM limit, e.g. `1g` (default `1g`)
- `CPU_LIMIT` — container CPU limit, e.g. `1.0` for one core (default `1.0`)
- `DB_SIZE_LIMIT_MB` — once the database exceeds this size, it switches to
  read-only until it shrinks back under the limit; `0` disables the limit
  (default `0`)

You can leave `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `API_KEY` unset — a
random database password and API key are generated on first run.

## 2. Deploy

```bash
./deploy.sh
```

This builds the image from the source tree (one level up) and (re)starts the
`sillysite` container, creating two named Docker volumes
(`sillysite_pgdata` and `sillysite_state`) to persist the database and
generated secrets across restarts/upgrades.

## 3. Retrieve the generated API key

If you didn't set `API_KEY` in `deploy.env`:

```bash
docker exec sillysite cat /var/lib/sillysite/secrets.env
```

This prints the generated `DB_PASSWORD` and `API_KEY`. The `API_KEY` value is
also printed once at container startup (`docker logs sillysite`). Use it as
the `X-API-Key` header (or `?apikey=` query parameter) — e.g. visit
`http://<host>:<API_PORT>/whoami.html?apikey=<API_KEY>`.

## Re-deploying after an update

Re-run `./deploy.sh`. It rebuilds the image and replaces the container, but
the database and secrets persist in the named volumes.

## Logs

```bash
docker logs -f sillysite
```

## Removing everything (including the database)

```bash
docker rm -f sillysite
docker volume rm sillysite_pgdata sillysite_state
```
