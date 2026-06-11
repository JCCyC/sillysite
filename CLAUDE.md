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
  CRUD endpoints for the Formula One data: `/teams`, `/drivers` (keyed by `car_number`), and
  `/grands-prix/{season}/{sequence_number}` (keyed by the composite season/sequence number).
- `config.py` loads database connection settings (`DB_HOST`, `DB_PORT`, `DB_SCHEMA`, `DB_NAME`,
  `DB_USER`, `DB_PASSWORD`) from environment variables / a `.env` file (see `.env.example`).
- `database.py` configures the SQLAlchemy engine/session from the values in `config.py`,
  connecting to PostgreSQL and setting the schema search path.
- `models.py` defines the Formula One data model: `Team`, `Driver`, and `GrandPrix`. Tables are
  created automatically on startup via `Base.metadata.create_all`.
- `schemas.py` defines the Pydantic request/response models used by the CRUD endpoints.
