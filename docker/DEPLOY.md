# Deploying SillySite

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
- `TLS_ENABLED` — `yes`/`no`, whether the API is served over HTTPS (default
  `yes`)

You can leave `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `API_KEY` unset — a
random database password and API key are generated on first run.

### HTTPS / TLS

With `TLS_ENABLED=yes` (the default), the API is served over HTTPS. Unless
you provide your own certificate (see below), a self-signed one is generated
automatically on first run — 100-year expiry, persisted in the `sillysite_state`
volume so it survives restarts/upgrades rather than being regenerated (and
therefore changing) every time. Because it isn't signed by any CA your
clients already trust, they'll need to explicitly trust or ignore it:

```bash
curl -k https://<host>:<API_PORT>/about                  # ignore the warning
# or, to actually trust it:
docker exec sillysite cat /var/lib/sillysite/tls/cert.pem > sillysite-cert.pem
curl --cacert sillysite-cert.pem https://<host>:<API_PORT>/about
```

By default the self-signed certificate only covers `localhost`/`127.0.0.1`.
If clients will reach the API by some other hostname or IP, set
`TLS_HOSTNAME` in `deploy.env` to that value before the first deploy (it has
no effect once a certificate already exists in the volume — remove
`/var/lib/sillysite/tls/` inside the container, or the whole `sillysite_state`
volume, and redeploy to regenerate it).

To use a real certificate instead (e.g. from Let's Encrypt or an internal
CA), set both `TLS_CERT_FILE` and `TLS_KEY_FILE` in `deploy.env` to host
paths (PEM format). Unlike the self-signed default, a provided certificate
is (re-)installed on *every* deploy, so rotating/renewing it is just:
replace the files at those paths and re-run `./deploy.sh`.

To disable HTTPS entirely and serve plain HTTP (e.g. if TLS is already
terminated by something in front of this container), set `TLS_ENABLED=no`.

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
`https://<host>:<API_PORT>/whoami.html?apikey=<API_KEY>` (`http://` if you
set `TLS_ENABLED=no`; see "HTTPS / TLS" above if using the self-signed
default certificate, since your browser will warn about it).

## Re-deploying after an update

Re-run `./deploy.sh`. It rebuilds the image and replaces the container, but
the database and secrets persist in the named volumes.

## Logs

```bash
docker logs -f sillysite
```

## Uninstalling

To stop and remove the container, but keep the database and secrets for a
future redeploy:

```bash
docker rm -f sillysite
```

To remove everything, including the database, generated secrets, the
self-signed TLS certificate (if any), and the built image:

```bash
docker rm -f sillysite
docker volume rm sillysite_pgdata sillysite_state
docker image rm sillysite
```
