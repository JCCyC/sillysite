# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal FastAPI app used for testing website deployment. All routes live in `main.py`.

## Commands

- Install dependencies: `pip install -r requirements.txt`
- Run the dev server: `uvicorn main:app --reload`

## Architecture

- `main.py` defines the FastAPI app and its endpoints (`/` and `/about`), each returning
  `{"msg": "<random message>"}` chosen from a small list of candidate messages.
