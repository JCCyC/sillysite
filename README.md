# Silly Site
Test for website deployment

A FastAPI app with:
- `/` and `/about`, which each return `{"msg": "<random message>"}`
- CRUD endpoints for Formula One data: `/teams`, `/drivers`, `/driver-numbers`, and
  `/grands-prix/{season}/{sequence_number}`, backed by PostgreSQL
- `/favicon.ico`

`GET` endpoints are public. `POST`/`PUT`/`DELETE` endpoints require an `X-API-Key` header
matching the `API_KEY` configured in the environment. `PUT` endpoints accept partial bodies —
only the fields provided are updated.

A Postman collection covering all endpoints is available in `postman_collection.json`.

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
